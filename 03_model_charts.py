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
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data import load_clean_data, build_regressor, get_model_report, NUM_FEATURES, CAT_FEATURES

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
# PHẦN 1: ĐÁNH GIÁ MÔ HÌNH RANDOM FOREST (cùng cấu hình với ứng dụng: data.build_regressor)
# =====================================================================
print("\n--- 1. ĐÁNH GIÁ HIỆU NĂNG RANDOM FOREST ---")
X = df[NUM_FEATURES + CAT_FEATURES]
y = df["log_price"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
rf_model = build_regressor().fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

report = get_model_report()  # cùng chia 80/20, random_state=42 -> trùng số liệu trong ứng dụng
print(f"Mô hình: Random Forest Regressor ({len(NUM_FEATURES)} biến số + {len(CAT_FEATURES)} biến phân loại)")
print(f"- R2 trên log giá : {report['r2_log']:.4f}")
print(f"- MAE (log)        : {report['mae_log']:.4f}")
print(f"- MAPE theo giá    : {report['mape_pct']:.1f}%")

plt.figure(figsize=(7, 6))
plt.scatter(y_test, y_pred, alpha=0.3, color="#2f6db5", s=10)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
plt.xlabel("Giá trị thực tế (log(1 + giá))")
plt.ylabel("Giá trị dự đoán (log(1 + giá))")
plt.title(f"Random Forest: Thực tế vs. Dự đoán (R² = {report['r2_log']:.3f}, MAPE ≈ {report['mape_pct']:.0f}%)")
save("10_rf_actual_vs_predicted.png")

# =====================================================================
# PHẦN 2: K-MEANS CLUSTERING (SLIDE 10)
# =====================================================================
print("\n--- 2. CHẠY K-MEANS & VẼ ELBOW ---")
Z_log = np.log1p(df[["Price_Billion_VND", "Land_Area"]])
Z_scaled = StandardScaler().fit_transform(Z_log)

K_range = range(1, 11)
wcss = []
for k in K_range:
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Z_scaled)
    wcss.append(km.inertia_)

plt.figure(figsize=(7, 5))
plt.plot(list(K_range), wcss, marker='o', color='#d9534f', lw=2)
plt.axvline(x=4, color='black', linestyle='--', label='K = 4 (được chọn)')
plt.title("Phương pháp Elbow: Tìm K tối ưu cho K-Means")
plt.xlabel("Số lượng cụm (K)")
plt.ylabel("WCSS (Tổng bình phương sai số)")
plt.legend()
save("11_kmeans_elbow.png")

kmeans_final = KMeans(n_clusters=4, n_init=15, random_state=42)
clusters = kmeans_final.fit_predict(Z_scaled)
Z_pca = PCA(n_components=2).fit_transform(Z_scaled)

# K-Means đánh số cụm NGẪU NHIÊN -> phải xếp hạng theo giá trung bình rồi mới gán nhãn
mean_price = pd.Series(df["Price_Billion_VND"].values).groupby(clusters).mean().sort_values()
rank_of = {cluster_id: rank for rank, cluster_id in enumerate(mean_price.index)}
names = ['Bình dân', 'Trung cấp', 'Cao cấp', 'Hạng sang']
colors = ['#3c9d6b', '#2f6db5', '#e0a030', '#d9534f']
print("Cụm theo giá trung bình tăng dần:", {names[rank_of[c]]: round(p, 1) for c, p in mean_price.items()})

plt.figure(figsize=(9, 6))
for cluster_id in mean_price.index:
    r = rank_of[cluster_id]
    mask = clusters == cluster_id
    plt.scatter(Z_pca[mask, 0], Z_pca[mask, 1], s=15, alpha=0.6, color=colors[r],
                label=f"{names[r]} (n={mask.sum()}, giá TB {mean_price[cluster_id]:.1f} tỷ)")
plt.title("Phân cụm thị trường BĐS bằng K-Means (theo giá + diện tích, trực quan hóa qua PCA)")
plt.xlabel("Thành phần chính 1 (PCA 1)")
plt.ylabel("Thành phần chính 2 (PCA 2)")
plt.legend()
save("12_kmeans_pca_clusters.png")

kmeans_final = KMeans(n_clusters=4, n_init=15, random_state=42)
clusters = kmeans_final.fit_predict(Z_scaled)
Z_pca = PCA(n_components=2).fit_transform(Z_scaled)

# K-Means đánh số cụm NGẪU NHIÊN -> phải xếp hạng theo giá trung bình rồi mới gán nhãn
mean_price = pd.Series(df["Price_Billion_VND"].values).groupby(clusters).mean().sort_values()
rank_of = {cluster_id: rank for rank, cluster_id in enumerate(mean_price.index)}
names = ['Bình dân', 'Trung cấp', 'Cao cấp', 'Hạng sang']
colors = ['#3c9d6b', '#2f6db5', '#e0a030', '#d9534f']
print("Cụm theo giá trung bình tăng dần:", {names[rank_of[c]]: round(p, 1) for c, p in mean_price.items()})

plt.figure(figsize=(9, 6))
for cluster_id in mean_price.index:
    r = rank_of[cluster_id]
    mask = clusters == cluster_id
    plt.scatter(Z_pca[mask, 0], Z_pca[mask, 1], s=15, alpha=0.6, color=colors[r],
                label=f"{names[r]} (n={mask.sum()}, giá TB {mean_price[cluster_id]:.1f} tỷ)")
plt.title("Phân cụm thị trường BĐS bằng K-Means (theo giá + diện tích, trực quan hóa qua PCA)")
plt.xlabel("Thành phần chính 1 (PCA 1)")
plt.ylabel("Thành phần chính 2 (PCA 2)")
plt.legend()
save("12_kmeans_pca_clusters.png")

# =====================================================================
# PHẦN 3: K-NEAREST NEIGHBORS (SLIDE 11)
# =====================================================================
print("\n--- 3. MINH HỌA THUẬT TOÁN KNN ---")
df_knn = df[df['Province'] == 'Hà Nội'].copy()
X_knn_raw = df_knn[["Land_Area", "Price_Billion_VND"]]
scaler_knn = StandardScaler()
X_knn_scaled = scaler_knn.fit_transform(np.log1p(X_knn_raw))

K_NEIGHBORS = 3
nn = NearestNeighbors(n_neighbors=K_NEIGHBORS, metric="euclidean").fit(X_knn_scaled)

TARGET_AREA, TARGET_PRICE = 80.0, 5.0
target_raw = pd.DataFrame([{"Land_Area": TARGET_AREA, "Price_Billion_VND": TARGET_PRICE}])
distances, indices = nn.kneighbors(scaler_knn.transform(np.log1p(target_raw)))

# Điểm khách hàng là điểm GIẢ ĐỊNH (không có trong dữ liệu) -> lấy cả 3 láng giềng gần nhất, không bỏ cái nào
neighbors_raw = X_knn_raw.iloc[indices[0]]

plt.figure(figsize=(9, 6))
plt.scatter(df_knn["Land_Area"], df_knn["Price_Billion_VND"], color='lightgray', alpha=0.5, s=20, label='Kho hàng thực tế (Hà Nội)')
for _, row in neighbors_raw.iterrows():
    plt.plot([TARGET_AREA, row["Land_Area"]], [TARGET_PRICE, row["Price_Billion_VND"]], color='#d9534f', linestyle='--', linewidth=1, alpha=0.7)
plt.scatter(neighbors_raw["Land_Area"], neighbors_raw["Price_Billion_VND"], color='#2f6db5', s=80, label=f'{K_NEIGHBORS} căn tương đồng nhất', edgecolors='black')
plt.scatter(TARGET_AREA, TARGET_PRICE, color='#d9534f', marker='*', s=300, label=f'Yêu cầu khách hàng ({TARGET_AREA:.0f} m², {TARGET_PRICE:.0f} tỷ)', edgecolors='black')

plt.xscale('log')
plt.yscale('log')
plt.title("Minh họa KNN: Tìm nhà tương đồng (Hà Nội)")
plt.xlabel("Diện tích (m², thang log)")
plt.ylabel("Giá bán (Tỷ VNĐ, thang log)")
plt.legend()
save("13_knn_neighborhood.png")

print("\nHOÀN TẤT!")