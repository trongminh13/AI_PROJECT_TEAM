"""Bước 2: phân tích khám phá dữ liệu (EDA) - vẽ 9 biểu đồ vào thư mục eda_charts/.
Biểu đồ 1 dùng file gốc (để thấy giá trị thiếu), các biểu đồ còn lại dùng file đã làm sạch.
Chạy: python 02_eda.py
"""

import sys
from pathlib import Path
import matplotlib

matplotlib.use("Agg")  # chỉ lưu ảnh, không mở cửa sổ UI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Thêm thư mục hiện tại vào sys.path để import common dù chạy từ bất kỳ đâu
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Thiết lập encoding UTF-8 cho console Windows tránh lỗi hiển thị tiếng Việt
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thiết lập font chữ tiếng Việt cho matplotlib (tránh lỗi font hình vuông / tofu)
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False  # Hiển thị đúng dấu trừ số âm

# Import cấu hình từ common.py (hoặc tự fallback nếu chạy độc lập)
try:
    from common import CHART_DIR, CLEAN_FILE, NUMERIC_COLS, RAW_FILE, TARGET
except ImportError:
    DATA_DIR = CURRENT_DIR / "data"
    CHART_DIR = CURRENT_DIR / "eda_charts"
    RAW_FILE = DATA_DIR / "Vietnam_Housing_Data_10000.xlsx" if (DATA_DIR / "Vietnam_Housing_Data_10000.xlsx").exists() else CURRENT_DIR / "Vietnam_Housing_Data_10000.xlsx"
    CLEAN_FILE = DATA_DIR / "housing_clean.csv" if (DATA_DIR / "housing_clean.csv").exists() else CURRENT_DIR / "housing_clean.csv"
    TARGET = "Price_Billion_VND"
    NUMERIC_COLS = [
        "Distance_To_Center", "Land_Area", "Floor_Area", "Floors", "Bedrooms",
        "Bathrooms", "House_Age", "Frontage", "Road_Width", "Distance_To_School",
        "Distance_To_Hospital", "Distance_To_Market"
    ]

# Đảm bảo thư mục lưu biểu đồ tồn tại
CHART_DIR.mkdir(exist_ok=True, parents=True)

print("Đang nạp dữ liệu...")
print(f"- File gốc: {RAW_FILE}")
raw = pd.read_excel(RAW_FILE, engine="openpyxl")  # file gốc, để vẽ biểu đồ 1

print(f"- File sạch: {CLEAN_FILE}")
df = pd.read_csv(CLEAN_FILE, encoding="utf-8-sig")
df["Log_Price"] = np.log(df[TARGET])


def save(filename):
    plt.tight_layout()
    output_path = CHART_DIR / filename
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✓ Đã lưu: {output_path}")


print("\n--- BẮT ĐẦU VẼ 9 BIỂU ĐỒ EDA ---")

# ---- 1. Tỷ lệ giá trị thiếu theo từng cột (file gốc) ----
missing = (raw.isna().mean() * 100).sort_values()
plt.figure(figsize=(9, 8))
plt.barh(missing.index, missing.values, color="#2f6db5")
for i, v in enumerate(missing.values):
    plt.text(v + 0.03, i, f"{v:.2f}%", va="center", fontsize=8)
plt.xlim(0, max(1.5, missing.max() * 1.35))
plt.xlabel("Tỷ lệ giá trị thiếu (%)")
plt.title("Tỷ lệ giá trị thiếu theo từng cột (file gốc)")
save("01_missing_values.png")

# ---- 2. Histogram giá và log giá ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(df[TARGET], bins=50, color="#2f6db5", edgecolor="white", linewidth=0.5)
axes[0].set_title(f"Giá nhà (độ lệch = {df[TARGET].skew():.2f})")
axes[0].set_xlabel("Giá (tỷ đồng)")
axes[0].set_ylabel("Số căn nhà")

axes[1].hist(df["Log_Price"], bins=50, color="#3c9d6b", edgecolor="white", linewidth=0.5)
axes[1].set_title(f"Log giá (độ lệch = {df['Log_Price'].skew():.2f})")
axes[1].set_xlabel("log(giá, tỷ đồng)")
save("02_price_histograms.png")

# ---- 3. Tương quan của từng cột số với log giá ----
corr = df[NUMERIC_COLS].corrwith(df["Log_Price"]).sort_values()
plt.figure(figsize=(8.5, 5.5))
plt.barh(corr.index, corr.values, color=["#d9534f" if v < 0 else "#2f6db5" for v in corr])
for i, v in enumerate(corr.values):
    plt.text(v + (0.015 if v >= 0 else -0.015), i, f"{v:.2f}", va="center",
             ha="left" if v >= 0 else "right", fontsize=9)
plt.axvline(0, color="black", linewidth=0.8)
plt.xlim(-0.6, 1.0)
plt.xlabel("Hệ số tương quan Pearson với log giá")
plt.title("Tương quan giữa các cột số và log giá")
save("03_correlation_with_log_price.png")

# ---- 4. Diện tích đất và giá (thang log), tô màu theo loại khu vực ----
plt.figure(figsize=(8.5, 6))
location_colors = [("Ngoại thành", "#3c9d6b"), ("Ven trung tâm", "#e0a030"), ("Trung tâm", "#d9534f")]
for location, color in location_colors:
    part = df[df["Location_Type"] == location]
    plt.scatter(part["Land_Area"], part[TARGET], s=8, alpha=0.45, color=color, label=location)
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Diện tích đất (m², thang log)")
plt.ylabel("Giá (tỷ đồng, thang log)")
plt.title("Diện tích đất và giá nhà theo loại khu vực")
plt.legend(markerscale=3)
save("04_land_area_vs_price.png")


# ---- 5 và 6. Boxplot log giá theo loại nhà / loại khu vực ----
def boxplot_by(column, title, filename):
    medians = df.groupby(column)[TARGET].median().sort_values()  # trung vị giá (tỷ đồng)
    groups = [df.loc[df[column] == g, "Log_Price"] for g in medians.index]
    plt.figure(figsize=(8.5, 5))
    plt.boxplot(groups)
    plt.xticks(range(1, len(groups) + 1), [f"{g}\n(trung vị {m:.1f} tỷ)" for g, m in medians.items()])
    plt.ylabel("log(giá, tỷ đồng)")
    plt.title(title)
    save(filename)


boxplot_by("Property_Type", "Log giá theo loại nhà", "05_price_by_property_type.png")
boxplot_by("Location_Type", "Log giá theo loại khu vực", "06_price_by_location_type.png")

# ---- 7. Khoảng cách tới trung tâm và giá/m² ----
plt.figure(figsize=(8.5, 5.5))
plt.scatter(df["Distance_To_Center"], df["Price_Per_m2"], s=7, alpha=0.35, color="#2f6db5")
bins = pd.cut(df["Distance_To_Center"], 12)
trend = df.groupby(bins, observed=True)["Price_Per_m2"].median()  # trung vị theo từng khoảng
plt.plot([b.mid for b in trend.index], trend.values, color="#d9534f", marker="o", linewidth=2, label="Trung vị theo khoảng")
plt.yscale("log")
plt.xlabel("Khoảng cách tới trung tâm (km)")
plt.ylabel("Giá/m² (triệu đồng, thang log)")
plt.title("Khoảng cách tới trung tâm và giá/m²")
plt.legend()
save("07_distance_vs_price_per_m2.png")

# ---- 8. Giá trung vị theo tỉnh/thành, kèm số tin ----
by_province = df.groupby("Province")[TARGET].agg(["median", "size"]).sort_values("median")
plt.figure(figsize=(9.5, 10.5))
plt.barh(by_province.index, by_province["median"], color="#2f6db5")
for i, (median, count) in enumerate(zip(by_province["median"], by_province["size"])):
    plt.text(median + 0.06, i, f"{median:.1f} tỷ | {count} tin", va="center", fontsize=8)
plt.xlim(0, by_province["median"].max() * 1.25)
plt.xlabel("Giá trung vị (tỷ đồng)")
plt.title("Giá trung vị theo tỉnh/thành (kèm số tin đăng)")
save("08_median_price_by_province.png")

# ---- 9. Heatmap tương quan giữa các cột số và log giá ----
order = corr.sort_values(ascending=False).index.tolist() + ["Log_Price"]
matrix = df[order].corr()
mask = np.triu(np.ones_like(matrix, dtype=bool), k=1)  # che nửa trên cho gọn
fig, ax = plt.subplots(figsize=(9, 7.5))
image = ax.imshow(np.ma.array(matrix.values, mask=mask), cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(order)))
ax.set_xticklabels(order, rotation=45, ha="right")
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order)
for i in range(len(order)):
    for j in range(i + 1):
        v = matrix.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                color="white" if abs(v) > 0.6 else "black")
fig.colorbar(image, ax=ax, shrink=0.8, label="Hệ số tương quan")
ax.set_title("Heatmap tương quan giữa các cột số và log giá")
save("09_correlation_heatmap.png")

# ---- Một vài số liệu để viết nhận xét trong báo cáo ----
print("\n=== THỐNG KÊ NHẬN XÉT EDA ===")
print("Tương quan với log giá:", corr.round(2).to_dict())
print("Giá trung vị theo loại nhà:", df.groupby("Property_Type")[TARGET].median().round(1).to_dict())
print("Giá trung vị theo loại khu vực:", df.groupby("Location_Type")[TARGET].median().round(1).to_dict())
print("5 tỉnh có nhiều tin nhất chiếm %.0f%% tổng số tin" % (df["Province"].value_counts().head(5).sum() / len(df) * 100))
print("=" * 60)
