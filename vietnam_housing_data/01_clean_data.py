"""Bước 1: làm sạch dữ liệu.
Đọc file gốc (Vietnam_Housing_Data_10000.xlsx) và lưu kết quả vào:
  - File CSV: data/housing_clean.csv (chuẩn dùng cho huấn luyện mô hình ML)
  - File Excel tương tự: data/Vietnam_Housing_Data_10000_clean.xlsx (file Excel tương tự file gốc nhưng đã sạch 100%)
File gốc không bị thay đổi. Chạy: python 01_clean_data.py
"""

import sys
from pathlib import Path
import pandas as pd

# Thêm thư mục hiện tại vào sys.path để import common dù chạy từ bất kỳ đâu
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Thiết lập encoding UTF-8 cho console Windows tránh lỗi hiển thị tiếng Việt
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Nhập các biến cấu hình từ common.py (hoặc dự phòng nếu chạy độc lập)
try:
    from common import (
        BOOL_COLS, CLEAN_EXCEL_FILE, CLEAN_FILE, DATA_DIR, FEATURES, ID_COLS, ORDINAL_ORDER, RAW_FILE, TARGET,
    )
except ImportError:
    DATA_DIR = CURRENT_DIR / "data"
    RAW_FILE = DATA_DIR / "Vietnam_Housing_Data_10000.xlsx" if (DATA_DIR / "Vietnam_Housing_Data_10000.xlsx").exists() else CURRENT_DIR / "Vietnam_Housing_Data_10000.xlsx"
    CLEAN_FILE = DATA_DIR / "housing_clean.csv"
    CLEAN_EXCEL_FILE = DATA_DIR / "Vietnam_Housing_Data_10000_clean.xlsx"
    ID_COLS = ["House_ID"]
    TARGET = "Price_Billion_VND"
    BOOL_COLS = ["Car_Access", "Parking", "Furniture_Included"]
    FEATURES = [
        "Province", "Ward", "District", "Street", "Location_Type", "Distance_To_Center",
        "Property_Type", "Land_Area", "Floor_Area", "Floors", "Bedrooms", "Bathrooms",
        "House_Age", "Frontage", "Architecture_Style", "Interior_Level",
        "Construction_Quality", "House_Condition", "Legal_Status", "Road_Width",
        "Car_Access", "Parking", "Distance_To_School", "Distance_To_Hospital",
        "Distance_To_Market", "Sale_Date", "Furniture_Included"
    ]
    ORDINAL_ORDER = {
        "Interior_Level": ["Chưa có nội thất", "Cơ bản", "Đầy đủ", "Cao cấp"],
        "Construction_Quality": ["Trung bình", "Khá", "Tốt", "Cao cấp"],
        "House_Condition": ["Xuống cấp", "Cần sửa chữa", "Tốt", "Mới"],
        "Location_Type": ["Ngoại thành", "Ven trung tâm", "Trung tâm"],
        "Legal_Status": ["Đang chờ giấy tờ", "Hợp đồng mua bán", "Sổ đỏ/Sổ hồng"]
    }

# Đọc file dữ liệu gốc
print(f"Đang đọc file gốc: {RAW_FILE}...")
df = pd.read_excel(RAW_FILE, engine="openpyxl")
print(f"File gốc: {len(df)} dòng, {df.shape[1]} cột")

# 1) Kiểm tra đủ cột cần dùng và giữ lại đúng các cột đó
needed = ID_COLS + [c for c in FEATURES if c not in ID_COLS] + [TARGET, "Price_Per_m2"]
needed = list(dict.fromkeys(needed))  # Giữ thứ tự và loại bỏ tên trùng nếu có
lacking = [c for c in needed if c not in df.columns]
if lacking:
    raise SystemExit(f"File gốc thiếu các cột: {lacking}")
df = df[needed]


def keep_rows(df, keep, reason):
    """Giữ lại các dòng thỏa điều kiện và in số dòng bị loại."""
    print(f"- {reason}: loại {int((~keep).sum())} dòng")
    return df[keep].copy()


print("\nCác bước làm sạch:")

# 2) Cắt khoảng trắng thừa ở các cột chữ
for col in df.columns:
    if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": pd.NA, "<NA>": pd.NA, "None": pd.NA})

# 3) Xóa dòng trùng (trùng mã nhà, hoặc trùng toàn bộ nội dung trừ mã nhà)
df = keep_rows(df, ~df["House_ID"].duplicated(), "Trùng mã nhà")
df = keep_rows(df, ~df.drop(columns="House_ID").duplicated(), "Trùng toàn bộ nội dung")

# 4) Giá trị thiếu: chỉ in thống kê rồi xóa các dòng có ô thiếu (tỷ lệ rất nhỏ: ~2.86%)
missing = df.isna().sum()
print("  Số ô thiếu theo cột:", missing[missing > 0].to_dict() or "không có")
df = keep_rows(df, ~df.isna().any(axis=1), "Có giá trị thiếu")

# 5) Giá trị không hợp lệ (âm, bằng 0 hoặc ngoài danh sách cho phép)
valid = (
    (df[TARGET] > 0) & (df["Price_Per_m2"] > 0)
    & (df["Land_Area"] > 0) & (df["Floor_Area"] > 0) & (df["Frontage"] > 0)
    & (df["Floors"] >= 1) & (df["Bedrooms"] >= 1) & (df["Bathrooms"] >= 1)
    & (df["House_Age"] >= 0) & (df["Distance_To_Center"] >= 0)
    & (df["Road_Width"] > 0) & (df["Distance_To_School"] >= 0)
    & (df["Distance_To_Hospital"] >= 0) & (df["Distance_To_Market"] >= 0)
)
for col, order in ORDINAL_ORDER.items():
    if col in df.columns:
        valid &= df[col].isin(order)
df = keep_rows(df, valid, "Giá trị không hợp lệ")

# 6) Ép kiểu: cột True/False về kiểu bool, cột ngày về datetime
for col in BOOL_COLS:
    if col in df.columns:
        df[col] = df[col].astype(bool)

if "Sale_Date" in df.columns:
    df["Sale_Date"] = pd.to_datetime(df["Sale_Date"])

# Không xóa outlier về giá: đó là các tin hợp lệ (nhà lớn, biệt thự đắt tiền)
print(f"\nGiá thấp nhất {df[TARGET].min():.2f} tỷ, cao nhất {df[TARGET].max():.2f} tỷ (giữ nguyên, không xóa)")

# 7) Tạo thư mục đầu ra và xuất kết quả
DATA_DIR.mkdir(exist_ok=True, parents=True)

# 7.1. Xuất file CSV sạch (UTF-8-SIG)
df.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
print(f"Đã lưu {len(df)} dòng, {df.shape[1]} cột vào {CLEAN_FILE}")

# 7.2. Tạo 1 file Excel tương tự từ dữ liệu đã làm sạch
df.to_excel(CLEAN_EXCEL_FILE, index=False, engine="openpyxl")
print(f"Đã tạo file Excel tương tự từ dữ liệu đã làm sạch: {CLEAN_EXCEL_FILE}")
