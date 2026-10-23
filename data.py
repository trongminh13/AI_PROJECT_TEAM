"""
Module: data.py
Quản lý nạp dữ liệu, làm sạch dị biệt, và khởi tạo/cache các mô hình Machine Learning:
- Random Forest Regressor: Dự đoán giá nhà (R² ~ 0.72, MAE ~ $98k)
- K-Means Clustering: Phân khúc 3 tầng thị trường (Bình dân, Trung cấp, Cao cấp)
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

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.csv")

_cached_data = None
_cached_reg_model = None
_cached_kmeans_model = None
_cached_kmeans_scaler = None
_cached_nn_model = None
_cached_nn_scaler = None
_feature_importances = None


def load_clean_data():
    """Đọc và làm sạch dữ liệu King County theo quy chuẩn EDA đã kiểm chứng."""
    global _cached_data
    if _cached_data is not None:
        return _cached_data.copy()

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {DATA_FILE}")

    df_raw = pd.read_csv(DATA_FILE)

    # 1. Loại bỏ các dòng dị biệt nghiêm trọng:
    # - 49 căn có price == 0
    # - 2 căn có bedrooms == 0 hoặc bathrooms == 0
    # - 1 căn typo tại Kent giá 26.59M USD (1.180 sqft)
    clean_mask = (
        (df_raw["price"] > 0)
        & (df_raw["bedrooms"] > 0)
        & (df_raw["bathrooms"] > 0)
        & (df_raw["price"] < 20000000)
    )
    df = df_raw[clean_mask].copy().reset_index(drop=True)

    # 2. Feature Engineering
    df["has_basement"] = (df["sqft_basement"] > 0).astype(int)
    df["is_renovated"] = (df["yr_renovated"] > 0).astype(int)
    df["log_sqft_lot"] = np.log1p(df["sqft_lot"])
    df["log_sqft_living"] = np.log1p(df["sqft_living"])
    df["log_price"] = np.log1p(df["price"])
    df["price_per_sqft"] = df["price"] / df["sqft_living"]

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

    # --- 1. RANDOM FOREST REGRESSION: DỰ ĐOÁN GIÁ ---
    num_features = [
        "bedrooms",
        "bathrooms",
        "sqft_living",
        "log_sqft_lot",
        "floors",
        "waterfront",
        "view",
        "condition",
        "yr_built",
        "is_renovated",
        "has_basement",
    ]
    cat_features = ["city"]

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
                    random_state=42,
                    n_jobs=-1,
                    max_depth=16,
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

    # --- 2. K-MEANS CLUSTERING: PHÂN KHÚC THỊ TRƯỜNG ---
    Z_raw = df[["price", "sqft_living"]]
    Z_log = np.log1p(Z_raw)
    kmeans_scaler = StandardScaler()
    Z_scaled = kmeans_scaler.fit_transform(Z_log)

    kmeans = KMeans(n_clusters=3, n_init=15, random_state=42)
    kmeans.fit(Z_scaled)

    # Sắp xếp nhãn cụm theo giá tăng dần (0: Bình dân, 1: Trung cấp, 2: Cao cấp)
    cluster_centers_log = kmeans_scaler.inverse_transform(kmeans.cluster_centers_)
    center_prices = np.expm1(cluster_centers_log[:, 0])
    label_order = np.argsort(center_prices)
    cluster_mapping = {old: new for new, old in enumerate(label_order)}

    _cached_kmeans_model = (kmeans, cluster_mapping)
    _cached_kmeans_scaler = kmeans_scaler

    # --- 3. NEAREST NEIGHBORS: TÌM NHÀ TƯƠNG ĐỒNG ---
    nn_features = ["sqft_living", "bedrooms", "bathrooms", "price"]
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
    print("Kiểm tra khởi tạo dữ liệu và mô hình...")
    df = load_clean_data()
    print(f"Số dòng dữ liệu sạch: {len(df)}")
    reg, km, km_scale, nn, nn_scale, feat_imp = get_trained_models()
    print("Huấn luyện mô hình thành công!")
    print("Top 5 đặc trưng quan trọng nhất:")
    print(feat_imp.head(5))
