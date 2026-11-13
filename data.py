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

# Nguồn duy nhất cho toàn bộ ứng dụng
DATA_FILE = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "data", "housing_clean.csv")

_cached_data = None
_cached_reg_model = None
_cached_kmeans_model = None
_cached_kmeans_scaler = None
_cached_nn_model = None
_cached_nn_scaler = None
_feature_importances = None

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
    if "price_per_m2" not in df.columns:
        df["price_per_m2"] = df["Price_Billion_VND"] * 1000 / df["Land_Area"]

    # Xử lý missing value
    df["Province"] = df["Province"].fillna("Không xác định")
    df["District"] = df["District"].fillna("Không xác định")
    df["Property_Type"] = df["Property_Type"].fillna("Nhà ở")
    df["Location_Type"] = df["Location_Type"].fillna("Ven trung tâm")

    _cached_data = df
    return _cached_data.copy()

def load_listing_data() -> pd.DataFrame:
    """
    Bí danh (Alias) để trỏ chung về tập 10k. 
    Giúp giao diện app.py và tools.py không bị lỗi khi chuyển từ kiến trúc 2 file sang 1 file.
    """
    return load_clean_data()

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
        "Land_Area", "Floor_Area", "Floors", "Bedrooms", "Bathrooms",
        "House_Age", "Frontage", "Road_Width", "Distance_To_Center",
        "Distance_To_School", "Distance_To_Hospital", "Distance_To_Market",
    ]
    cat_features = ["Province", "Property_Type", "Location_Type"]

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
    ])

    reg_pipeline = Pipeline([
        ("prep", preprocessor),
        ("rf", RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=4, min_samples_split=10, max_features=0.8, random_state=42, n_jobs=-1)),
    ])

    X = df[num_features + cat_features]
    y_log = df["log_price"]
    reg_pipeline.fit(X, y_log)
    _cached_reg_model = reg_pipeline

    # Trích xuất Feature Importance
    rf_step = reg_pipeline.named_steps["rf"]
    prep_step = reg_pipeline.named_steps["prep"]
    encoded_cat_names = prep_step.named_transformers_["cat"].get_feature_names_out(cat_features)
    all_feature_names = list(num_features) + list(encoded_cat_names)
    _feature_importances = pd.Series(rf_step.feature_importances_, index=all_feature_names).sort_values(ascending=False)

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