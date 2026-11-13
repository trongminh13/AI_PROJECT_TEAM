"""
Module: data.py
Quản lý nạp dữ liệu, làm sạch dị biệt, và khởi tạo/cache các mô hình Machine Learning.
Kiến trúc Single-Source: Sử dụng duy nhất tập housing_clean.csv (từ 10k dòng ban đầu).
- Random Forest Regressor: Dự đoán giá nhà (Tỷ VNĐ)
- K-Means Clustering: Phân khúc 4 tầng thị trường
- KNN / Nearest Neighbors: Tìm kiếm căn nhà tương đồng
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import re
import unicodedata

# Nguồn duy nhất cho toàn bộ ứng dụng
DATA_FILE = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "data", "housing_clean.csv")

_cached_data = None
_cached_reg_model = None
_cached_kmeans_model = None
_cached_kmeans_scaler = None
_cached_nn_model = None
_cached_nn_scaler = None
_feature_importances = None

# ---------------------------------------------------------------------------
# HẰNG SỐ DÙNG CHUNG (một nguồn duy nhất cho app, tools, agent, 03_model_charts)
# ---------------------------------------------------------------------------
NUM_FEATURES = [
    "Land_Area", "Floor_Area", "Floors", "Bedrooms", "Bathrooms",
    "House_Age", "Frontage", "Road_Width", "Distance_To_Center",
    "Distance_To_School", "Distance_To_Hospital", "Distance_To_Market",
]
CAT_FEATURES = ["Province", "Property_Type", "Location_Type"]

FEATURE_LABELS = {
    "Land_Area": "Diện tích đất", "Floor_Area": "Diện tích sàn", "Floors": "Số tầng",
    "Bedrooms": "Phòng ngủ", "Bathrooms": "Phòng tắm", "House_Age": "Tuổi nhà",
    "Frontage": "Mặt tiền", "Road_Width": "Đường rộng", "Distance_To_Center": "Cách trung tâm",
    "Distance_To_School": "Cách trường", "Distance_To_Hospital": "Cách bệnh viện",
    "Distance_To_Market": "Cách chợ", "Province": "Tỉnh/Thành", "Property_Type": "Loại nhà",
    "Location_Type": "Loại khu vực",
}

# Phân khúc theo ngưỡng giá (tỷ VNĐ): ĐỊNH NGHĨA DUY NHẤT cho toàn dự án
SEGMENT_BINS = [
    ("Bình dân", 0.0, 2.0),
    ("Trung cấp", 2.0, 5.0),
    ("Cao cấp", 5.0, 15.0),
    ("Hạng sang", 15.0, float("inf")),
]

def classify_segment(price_billion: float) -> str:
    """Trả về tên phân khúc theo ngưỡng giá: <2, 2-5, 5-15, >15 tỷ."""
    for name, lo, hi in SEGMENT_BINS:
        if lo <= price_billion < hi:
            return name
    return SEGMENT_BINS[-1][0]

# ---------------------------------------------------------------------------
# CHUẨN HÓA TÊN TỈNH/THÀNH (không phân biệt hoa thường, dấu, "TP.")
# ---------------------------------------------------------------------------
PROVINCE_ALIASES = {
    "hcm": "TP. Hồ Chí Minh", "tphcm": "TP. Hồ Chí Minh", "sai gon": "TP. Hồ Chí Minh",
    "hn": "Hà Nội", "ha noi": "Hà Nội",
}

def normalize_text(s) -> str:
    s = unicodedata.normalize("NFD", str(s).lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"^(tp|thanh pho) ", "", s)

def match_province(name, provinces):
    """Khớp tên tỉnh người dùng nhập với tên chuẩn trong dữ liệu. Không khớp -> None."""
    n = normalize_text(name)
    if not n:
        return None
    norm_map = {normalize_text(p): p for p in provinces}
    if n in norm_map:
        return norm_map[n]
    alias = PROVINCE_ALIASES.get(n)
    if alias in provinces:
        return alias
    if len(n) >= 4:
        for key, p in norm_map.items():
            if n in key or key in n:
                return p
    return None

def find_province_in_text(text, provinces):
    """Tìm tên tỉnh/thành xuất hiện trong một câu hỏi tự do (dùng cho chế độ offline)."""
    t = f" {normalize_text(text)} "
    cands = {normalize_text(p): p for p in provinces}
    cands.update({k: v for k, v in PROVINCE_ALIASES.items() if v in provinces})
    for key in sorted(cands, key=len, reverse=True):
        if f" {key} " in t:
            return cands[key]
    return None

def load_clean_data() -> pd.DataFrame:
    """Đọc và làm sạch dữ liệu nhà ở Việt Nam từ file CSV đã được chuẩn hóa."""
    global _cached_data
    if _cached_data is not None:
        return _cached_data.copy()

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu sạch: {DATA_FILE}. Vui lòng chạy 01_clean_data.py trước.")

    df_raw = pd.read_csv(DATA_FILE)

    # Lọc dị biệt (nếu còn sót)
    clean_mask = (
        (df_raw["Price_Billion_VND"] > 0)
        & (df_raw["Land_Area"] > 0)
        & (df_raw["Bedrooms"] > 0)
        & (df_raw["Price_Billion_VND"] < 500)
    )
    df = df_raw[clean_mask].copy().reset_index(drop=True)

    # Feature Engineering
    df["log_land_area"] = np.log1p(df["Land_Area"])
    df["log_floor_area"] = np.log1p(df["Floor_Area"])
    df["log_price"] = np.log1p(df["Price_Billion_VND"])
    # Đơn giá (triệu/m²) = giá * 1000 / diện tích đất; dùng lại cột gốc Price_Per_m2 nếu có
    df["price_per_m2"] = df["Price_Per_m2"] if "Price_Per_m2" in df.columns else df["Price_Billion_VND"] * 1000 / df["Land_Area"]

    _cached_data = df
    return _cached_data.copy()

def load_listing_data() -> pd.DataFrame:
    """
    Bí danh (Alias) để trỏ chung về tập 10k. 
    Giúp giao diện app.py và tools.py không bị lỗi khi chuyển từ kiến trúc 2 file sang 1 file.
    """
    return load_clean_data()

_model_report = {}

def build_regressor() -> Pipeline:
    """Pipeline Random Forest dùng chung cho app và 03_model_charts.py (một cấu hình duy nhất)."""
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUM_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
    ])
    return Pipeline([
        ("prep", preprocessor),
        ("rf", RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=4,
             min_samples_split=10, max_features=0.8, random_state=42, n_jobs=-1)),
    ])

def get_model_report() -> dict:
    """Chỉ số đánh giá trên tập kiểm tra (R² trên log giá, MAPE %, phân vị 10/90 của sai số log)."""
    get_trained_models()
    return dict(_model_report)

def segment_table() -> list:
    """Thống kê thật của 4 phân khúc theo ngưỡng giá (dùng cho thẻ phân khúc và công cụ)."""
    df = load_clean_data()
    out = []
    for name, lo, hi in SEGMENT_BINS:
        part = df[(df["Price_Billion_VND"] >= lo) & (df["Price_Billion_VND"] < hi)]
        top_type = part["Property_Type"].value_counts()
        out.append({
            "name": name, "min": lo, "max": hi, "count": int(len(part)),
            "share_pct": round(len(part) / len(df) * 100, 1),
            "median_price": round(float(part["Price_Billion_VND"].median()), 2),
            "mean_land_area": round(float(part["Land_Area"].mean()), 0),
            "median_bedrooms": int(part["Bedrooms"].median()),
            "median_floors": int(part["Floors"].median()),
            "top_property_type": str(top_type.index[0]),
            "top_property_share_pct": round(float(top_type.iloc[0] / len(part) * 100), 0),
        })
    return out

def get_trained_models():
    """Khởi tạo và huấn luyện các mô hình ML (chạy một lần và cache vào bộ nhớ)."""
    global _cached_reg_model, _cached_kmeans_model, _cached_kmeans_scaler
    global _cached_nn_model, _cached_nn_scaler, _feature_importances

    if _cached_reg_model is not None:
        return (
            _cached_reg_model,
            _cached_kmeans_model,
            _cached_kmeans_scaler,
            _cached_nn_model,
            _cached_nn_scaler,
            _feature_importances,
        )

    df = load_clean_data()

    # --- 1. RANDOM FOREST REGRESSION: DỰ ĐOÁN GIÁ (Tỷ VNĐ) ---
    num_features, cat_features = NUM_FEATURES, CAT_FEATURES
    X = df[num_features + cat_features]
    y_log = df["log_price"]

    # 1a. Đánh giá trên tập kiểm tra 20% -> R², MAPE và phân vị sai số để tạo khoảng giá
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_log, test_size=0.2, random_state=42)
    eval_model = build_regressor().fit(X_tr, y_tr)
    pred_te = eval_model.predict(X_te)
    actual_te, pred_price_te = np.expm1(y_te.values), np.expm1(pred_te)
    _model_report.update({
        "r2_log": float(r2_score(y_te, pred_te)),
        "mae_log": float(mean_absolute_error(y_te, pred_te)),
        "mape_pct": float(np.mean(np.abs(pred_price_te - actual_te) / actual_te) * 100),
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    })

    # 1b. Huấn luyện lại trên toàn bộ dữ liệu cho mô hình dùng trong ứng dụng
    reg_pipeline = build_regressor().fit(X, y_log)
    _cached_reg_model = reg_pipeline

    # Feature importance: GỘP các cột one-hot về biến gốc (Province_Hà Nội, ... -> Province)
    rf_step = reg_pipeline.named_steps["rf"]
    prep_step = reg_pipeline.named_steps["prep"]
    encoded_cat_names = prep_step.named_transformers_["cat"].get_feature_names_out(cat_features)
    all_feature_names = list(num_features) + list(encoded_cat_names)
    raw_imp = pd.Series(rf_step.feature_importances_, index=all_feature_names)
    grouped = {}
    for name, val in raw_imp.items():
        base = next((c for c in cat_features if name.startswith(c + "_")), name)
        grouped[base] = grouped.get(base, 0.0) + float(val)
    _feature_importances = pd.Series(grouped).sort_values(ascending=False)

    # --- 2. K-MEANS CLUSTERING: PHÂN KHÚC THỊ TRƯỜNG ---
    Z_log = np.log1p(df[["Price_Billion_VND", "Land_Area"]])
    kmeans_scaler = StandardScaler()
    Z_scaled = kmeans_scaler.fit_transform(Z_log)

    kmeans = KMeans(n_clusters=4, n_init=15, random_state=42)
    kmeans.fit(Z_scaled)

    cluster_centers_log = kmeans_scaler.inverse_transform(kmeans.cluster_centers_)
    center_prices = np.expm1(cluster_centers_log[:, 0])
    label_order = np.argsort(center_prices)
    cluster_mapping = {old: new for new, old in enumerate(label_order)}

    _cached_kmeans_model = (kmeans, cluster_mapping)
    _cached_kmeans_scaler = kmeans_scaler

    # --- 3. NEAREST NEIGHBORS: CHUẨN HÓA KHOẢNG CÁCH KNN ---
    nn_features = ["Price_Billion_VND", "Land_Area", "Bedrooms"]
    nn_scaler = StandardScaler()
    nn_scaler.fit(np.log1p(df[nn_features]))
    
    _cached_nn_model = None # KNN sẽ được khởi tạo động (On-the-fly) bên trong tools.py
    _cached_nn_scaler = nn_scaler

    return (
        _cached_reg_model,
        _cached_kmeans_model,
        _cached_kmeans_scaler,
        _cached_nn_model,
        _cached_nn_scaler,
        _feature_importances,
    )