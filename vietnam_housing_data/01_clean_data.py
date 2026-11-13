"""Bước 1: làm sạch dữ liệu.
Đọc file gốc (Vietnam_Housing_Data_10000.xlsx) và lưu kết quả vào:
  - File CSV: data/housing_clean.csv (chuẩn dùng cho huấn luyện mô hình ML & tìm kiếm)
  - File Excel tương tự: data/Vietnam_Housing_Data_10000_clean.xlsx
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
from common import (
    BOOL_COLS, CLEAN_EXCEL_FILE, CLEAN_FILE, DATA_DIR, FEATURES, ID_COLS, ORDINAL_ORDER, RAW_FILE, TARGET,
)

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

# 4) Giá trị thiếu
missing = df.isna().sum()
print("  Số ô thiếu theo cột:", missing[missing > 0].to_dict() or "không có")
df = keep_rows(df, ~df.isna().any(axis=1), "Có giá trị thiếu")

# 5) Giá trị không hợp lệ
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

# 6) Ép kiểu
for col in BOOL_COLS:
    if col in df.columns:
        df[col] = df[col].astype(bool)

if "Sale_Date" in df.columns:
    df["Sale_Date"] = pd.to_datetime(df["Sale_Date"])

print(f"\nGiá thấp nhất {df[TARGET].min():.2f} tỷ, cao nhất {df[TARGET].max():.2f} tỷ (giữ nguyên, không xóa)")

# 7) Tạo thư mục đầu ra và xuất kết quả
DATA_DIR.mkdir(exist_ok=True, parents=True)

# 7.1. Xuất file CSV sạch 
df.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
print(f"Đã lưu {len(df)} dòng, {df.shape[1]} cột vào {CLEAN_FILE}")

# 7.2. Tạo 1 file Excel tương tự từ dữ liệu đã làm sạch
df.to_excel(CLEAN_EXCEL_FILE, index=False, engine="openpyxl")
print(f"Đã tạo file Excel tương tự từ dữ liệu đã làm sạch: {CLEAN_EXCEL_FILE}")