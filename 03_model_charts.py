"""
Bước 3: Đánh giá Mô hình Random Forest & Vẽ biểu đồ K-Means, KNN
Chạy: python 03_model_charts.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data import load_clean_data

plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CHART_DIR = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "eda_charts")
os.makedirs(CHART_DIR, exist_ok=True)

def save(filename):
    plt.tight_layout()
    output_path = os.path.join(CHART_DIR, filename)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Đã lưu biểu đồ: {filename}")

df = load_clean_data()

# =====================================================================
# PHẦN 1: ĐÁNH GIÁ MÔ HÌNH RANDOM FOREST (SLIDE 8 & 9)
# =====================================================================
print("\n--- 1. ĐÁNH GIÁ HIỆU NĂNG RANDOM FOREST ---")
num_features = ["Land_Area", "Floor_Area", "Floors", "Bedrooms", "Bathrooms", "Distance_To_Center"]
cat_features = ["Province", "Property_Type", "Location_Type"]

X = df[num_features + cat_features]
y = df["log_price"] 

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), num_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
])
X_processed = preprocessor.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)

rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"Mô hình: Random Forest Regressor")
print(f"- R2 Score (Độ giải thích): {r2:.4f}")
print(f"- MAE (Sai số tuyệt đối): {mae:.4f}")
print(f"- RMSE (Sai số bình phương): {rmse:.4f}")

# Vẽ biểu đồ Actual vs Predicted
plt.figure(figsize=(7, 6))
plt.scatter(y_test, y_pred, alpha=0.3, color="#2f6db5", s=10)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
plt.xlabel("Giá trị thực tế (Log Price)")
plt.ylabel("Giá trị dự đoán (Log Price)")
plt.title("Random Forest: Thực tế vs. Dự đoán")
save("10_rf_actual_vs_predicted.png")

# =====================================================================
# PHẦN 2: K-MEANS CLUSTERING (SLIDE 10)
# =====================================================================
print("\n--- 2. CHẠY K-MEANS & VẼ ELBOW, PCA ---")
Z_log = np.log1p(df[["Price_Billion_VND", "Land_Area"]])
scaler_km = StandardScaler()
Z_scaled = scaler_km.fit_transform(Z_log)

wcss = []
K_range = range(1, 11)
for k in K_range:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(Z_scaled)
    wcss.append(km.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(K_range, wcss, marker='o', linestyle='-', color='#d9534f', lw=2)
plt.axvline(x=4, color='black', linestyle='--', label='Điểm cùi chỏ (K=4)')
plt.title("Phương pháp Elbow tìm số cụm K tối ưu")
plt.xlabel("Số lượng cụm (K)")
plt.ylabel("WCSS (Tổng bình phương sai số)")
plt.legend()
save("11_kmeans_elbow.png")

kmeans_final = KMeans(n_clusters=4, n_init=15, random_state=42)
clusters = kmeans_final.fit_predict(Z_scaled)
pca = PCA(n_components=2)
Z_pca = pca.fit_transform(Z_scaled)

plt.figure(figsize=(9, 6))
colors = ['#3c9d6b', '#2f6db5', '#e0a030', '#d9534f']
labels = ['Bình dân', 'Trung cấp', 'Cao cấp', 'Hạng sang']
for i in range(4):
    plt.scatter(Z_pca[clusters == i, 0], Z_pca[clusters == i, 1], s=15, alpha=0.6, color=colors[i], label=labels[i])
plt.title("Phân cụm thị trường BĐS bằng K-Means (Trực quan hóa qua PCA)")
plt.xlabel("Thành phần chính 1 (PCA 1)")
plt.ylabel("Thành phần chính 2 (PCA 2)")
plt.legend()
save("12_kmeans_pca_clusters.png")

# =====================================================================
# PHẦN 3: K-NEAREST NEIGHBORS (SLIDE 11)
# =====================================================================
print("\n--- 3. MINH HỌA THUẬT TOÁN KNN ---")
df_knn = df[(df['Province'] == 'Hà Nội')].copy()
X_knn_raw = df_knn[["Land_Area", "Price_Billion_VND"]]
scaler_knn = StandardScaler()
X_knn_scaled = scaler_knn.fit_transform(np.log1p(X_knn_raw))

nn = NearestNeighbors(n_neighbors=4, metric="euclidean")
nn.fit(X_knn_scaled)

target_raw = pd.DataFrame([{"Land_Area": 80.0, "Price_Billion_VND": 5.0}])
target_scaled = scaler_knn.transform(np.log1p(target_raw))
distances, indices = nn.kneighbors(target_scaled)

plt.figure(figsize=(9, 6))
plt.scatter(df_knn["Land_Area"], df_knn["Price_Billion_VND"], color='lightgray', alpha=0.5, s=20, label='Kho hàng thực tế (Hà Nội)')
neighbors_idx = indices[0][1:]
neighbors_raw = X_knn_raw.iloc[neighbors_idx]
plt.scatter(neighbors_raw["Land_Area"], neighbors_raw["Price_Billion_VND"], color='#2f6db5', s=80, label='3 Căn Tương Đồng Nhất', edgecolors='black')
plt.scatter(80, 5, color='#d9534f', marker='*', s=300, label='Yêu cầu khách hàng (80m2, 5 tỷ)', edgecolors='black')

radius = distances[0][-1] * 50
circle = plt.Circle((80, 5), radius=10, color='red', fill=False, linestyle='--', linewidth=1.5, alpha=0.7)
plt.gca().add_patch(circle)

plt.xscale('log')
plt.yscale('log')
plt.title("Minh họa KNN: Tìm nhà tương đồng (Hà Nội)")
plt.xlabel("Diện tích (m², Log scale)")
plt.ylabel("Giá bán (Tỷ VNĐ, Log scale)")
plt.legend()
save("13_knn_neighborhood.png")

print("\nHOÀN TẤT!")