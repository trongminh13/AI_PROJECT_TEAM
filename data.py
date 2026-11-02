"""
Module: data.py
Quản lý nạp dữ liệu, làm sạch dị biệt, và khởi tạo/cache các mô hình Machine Learning
cho thị trường bất động sản Việt Nam:
- Random Forest Regressor: Dự đoán giá nhà (Tỷ VNĐ) — nguồn: housing_clean.csv (9,714 dòng)
- K-Means Clustering: Phân khúc 4 tầng thị trường — nguồn: housing_clean.csv
- KNN / Nearest Neighbors: Tìm kiếm căn nhà tương đồng — nguồn: housing_clean.csv

Kiến trúc Dual-Source (theo đề xuất Senior QA):
  - load_clean_data()   → housing_clean.csv  (ML training, đặc trưng khoảng cách chuẩn hóa)
  - load_listing_data() → house_cleaned.csv  (find_similar_houses, địa chỉ & dự án thực tế)
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

# Nguồn 1: Dữ liệu ML (features khoảng cách chuẩn hóa, 9,714 dòng sạch)
DATA_FILE = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "data", "housing_clean.csv")

# Nguồn 2: Dữ liệu listing thực tế (địa chỉ thật, tên dự án Vinhomes, 30,078 dòng)
LISTING_FILE = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "house_cleaned.csv")

_cached_data = None
_cached_listing_data = None
_cached_reg_model = None
_cached_kmeans_model = None
_cached_kmeans_scaler = None
_cached_nn_model = None
_cached_nn_scaler = None
_feature_importances = None

# Bảng alias chuẩn hóa tên tỉnh/thành giữa 2 file CSV
_PROVINCE_ALIAS = {
    "Hồ Chí Minh": "TP. Hồ Chí Minh",
    "TP Hồ Chí Minh": "TP. Hồ Chí Minh",
    "TP.HCM": "TP. Hồ Chí Minh",
    "TPHCM": "TP. Hồ Chí Minh",
    "HCM": "TP. Hồ Chí Minh",
    "Thừa Thiên Huế": "Huế",
    "Thua Thien Hue": "Huế",
}


def _normalize_province(name: str) -> str:
    """Chuẩn hóa tên tỉnh/thành để so sánh cross-file (housing_clean ↔ house_cleaned)."""
    name = str(name).strip()
    return _PROVINCE_ALIAS.get(name, name)


def load_listing_data() -> pd.DataFrame:
    """Đọc house_cleaned.csv (30,078 dòng) — nguồn listing thực tế cho find_similar_houses.
    Chứa địa chỉ nhà thật, đường phố thật, tên dự án Vinhomes thật.
    """
    global _cached_listing_data
    if _cached_listing_data is not None:
        return _cached_listing_data.copy()

    if not os.path.exists(LISTING_FILE):
        raise FileNotFoundError(f"Không tìm thấy file listing: {LISTING_FILE}")

    df = pd.read_csv(LISTING_FILE)

    # Rename sang tên cột nhất quán với hệ thống
    df = df.rename(columns={
        "Land_Area_m2": "Land_Area",
        "Floors_Count": "Floors",
        "Bedrooms_Count": "Bedrooms",
        "Bathrooms_Count": "Bathrooms",
        "Price_per_m2_million": "price_per_m2",
    })

    # Normalize Province để tìm kiếm cross-file đúng
    df["Province_norm"] = df["Province"].apply(_normalize_province)

    # Lọc dòng giá hợp lệ
    df = df[df["Price_Billion_VND"] > 0].reset_index(drop=True)

    _cached_listing_data = df
    return _cached_listing_data.copy()


def load_clean_data():
    """Đọc và làm sạch dữ liệu nhà ở Việt Nam theo quy chuẩn EDA đã kiểm chứng."""
    global _cached_data
    if _cached_data is not None:
        return _cached_data.copy()

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {DATA_FILE}")

    df_raw = pd.read_csv(DATA_FILE)

    # 1. Loại bỏ các dòng dị biệt nghiêm trọng
    clean_mask = (
        (df_raw["Price_Billion_VND"] > 0)
        & (df_raw["Land_Area"] > 0)
        & (df_raw["Bedrooms"] > 0)
        & (df_raw["Price_Billion_VND"] < 500)  # Lọc outlier cực đoan (>500 tỷ)
    )
    df = df_raw[clean_mask].copy().reset_index(drop=True)

    # 2. Feature Engineering
    df["log_land_area"] = np.log1p(df["Land_Area"])
    df["log_floor_area"] = np.log1p(df["Floor_Area"])
    df["log_price"] = np.log1p(df["Price_Billion_VND"])
    df["price_per_m2"] = df["Price_Billion_VND"] * 1000 / df["Land_Area"]  # Triệu VNĐ/m²

    # 3. Chuẩn hóa Province - đảm bảo không null
    df["Province"] = df["Province"].fillna("Không xác định")
    df["District"] = df["District"].fillna("Không xác định")
    df["Property_Type"] = df["Property_Type"].fillna("Nhà ở")
    df["Location_Type"] = df["Location_Type"].fillna("Ven trung tâm")

    _cached_data = df
    return _cached_data.copy()


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
    num_features = [
        "Land_Area",
        "Floor_Area",
        "Floors",
        "Bedrooms",
        "Bathrooms",
        "House_Age",
        "Frontage",
        "Road_Width",
        "Distance_To_Center",
        "Distance_To_School",
        "Distance_To_Hospital",
        "Distance_To_Market",
    ]
    cat_features = ["Province", "Property_Type", "Location_Type"]

    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
        ]
    )

    reg_pipeline = Pipeline(
        [
            ("prep", preprocessor),
            (
                "rf",
                RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_leaf=4,
                    min_samples_split=10,
                    max_features=0.8,
                    oob_score=True,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    X = df[num_features + cat_features]
    y_log = df["log_price"]
    reg_pipeline.fit(X, y_log)
    _cached_reg_model = reg_pipeline

    # Trích xuất Feature Importance
    rf_step = reg_pipeline.named_steps["rf"]
    prep_step = reg_pipeline.named_steps["prep"]
    encoded_cat_names = prep_step.named_transformers_["cat"].get_feature_names_out(cat_features)
    all_feature_names = list(num_features) + list(encoded_cat_names)
    importances = pd.Series(rf_step.feature_importances_, index=all_feature_names).sort_values(ascending=False)
    _feature_importances = importances

    # --- 2. K-MEANS CLUSTERING: PHÂN KHÚC THỊ TRƯỜNG (4 tầng VN) ---
    Z_raw = df[["Price_Billion_VND", "Land_Area"]]
    Z_log = np.log1p(Z_raw)
    kmeans_scaler = StandardScaler()
    Z_scaled = kmeans_scaler.fit_transform(Z_log)

    kmeans = KMeans(n_clusters=4, n_init=15, random_state=42)
    kmeans.fit(Z_scaled)

    # Sắp xếp nhãn cụm theo giá tăng dần (0: Bình dân → 3: Hạng sang)
    cluster_centers_log = kmeans_scaler.inverse_transform(kmeans.cluster_centers_)
    center_prices = np.expm1(cluster_centers_log[:, 0])
    label_order = np.argsort(center_prices)
    cluster_mapping = {old: new for new, old in enumerate(label_order)}

    _cached_kmeans_model = (kmeans, cluster_mapping)
    _cached_kmeans_scaler = kmeans_scaler

    # --- 3. NEAREST NEIGHBORS: TÌM NHÀ TƯƠNG ĐỒNG ---
    nn_features = ["Land_Area", "Bedrooms", "Bathrooms", "Price_Billion_VND"]
    nn_scaler = StandardScaler()
    scaled_nn_data = nn_scaler.fit_transform(np.log1p(df[nn_features]))
    nn_model = NearestNeighbors(n_neighbors=10, metric="euclidean")
    nn_model.fit(scaled_nn_data)

    _cached_nn_model = nn_model
    _cached_nn_scaler = nn_scaler

    return (
        _cached_reg_model,
        _cached_kmeans_model,
        _cached_kmeans_scaler,
        _cached_nn_model,
        _cached_nn_scaler,
        _feature_importances,
    )


if __name__ == "__main__":
    print("Kiểm tra khởi tạo dữ liệu và mô hình (Vietnam Housing)...")
    df = load_clean_data()
    print(f"Số dòng dữ liệu sạch: {len(df)}")
    print(f"Các tỉnh thành: {sorted(df['Province'].unique())[:10]}")
    reg, km, km_scale, nn, nn_scale, feat_imp = get_trained_models()
    print("Huấn luyện mô hình thành công!")
    print("Top 5 đặc trưng quan trọng nhất:")
    print(feat_imp.head(5))
