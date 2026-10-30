"""
Module cấu hình chung cho dự án phân tích & dự đoán giá bất động sản Việt Nam.
Chứa các hằng số, danh sách thuộc tính và đường dẫn file dữ liệu.
"""

from pathlib import Path

# Cấu hình thư mục và đường dẫn file (tương đối theo vị trí file common.py)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHART_DIR = BASE_DIR / "eda_charts"

RAW_FILE = (
    (DATA_DIR / "Vietnam_Housing_Data_10000.xlsx")
    if (DATA_DIR / "Vietnam_Housing_Data_10000.xlsx").exists()
    else (BASE_DIR / "Vietnam_Housing_Data_10000.xlsx")
)
CLEAN_FILE = DATA_DIR / "housing_clean.csv"
CLEAN_EXCEL_FILE = DATA_DIR / "Vietnam_Housing_Data_10000_clean.xlsx"

# Nhóm cột định danh và cột mục tiêu (Target)
ID_COLS = ["House_ID"]
TARGET = "Price_Billion_VND"

# Cột kiểu True/False (Boolean)
BOOL_COLS = ["Car_Access", "Parking", "Furniture_Included"]

# Danh sách các cột số dùng cho EDA & mô hình hóa
NUMERIC_COLS = [
    "Distance_To_Center", "Land_Area", "Floor_Area", "Floors", "Bedrooms",
    "Bathrooms", "House_Age", "Frontage", "Road_Width", "Distance_To_School",
    "Distance_To_Hospital", "Distance_To_Market"
]

# Danh sách các đặc trưng (Features)
FEATURES = [
    "Province", "Ward", "District", "Street", "Location_Type", "Distance_To_Center",
    "Property_Type", "Land_Area", "Floor_Area", "Floors", "Bedrooms", "Bathrooms",
    "House_Age", "Frontage", "Architecture_Style", "Interior_Level",
    "Construction_Quality", "House_Condition", "Legal_Status", "Road_Width",
    "Car_Access", "Parking", "Distance_To_School", "Distance_To_Hospital",
    "Distance_To_Market", "Sale_Date", "Furniture_Included"
]

# Thứ bậc và giá trị hợp lệ cho các biến phân loại có thứ tự (Ordinal)
ORDINAL_ORDER = {
    "Interior_Level": ["Chưa có nội thất", "Cơ bản", "Đầy đủ", "Cao cấp"],
    "Construction_Quality": ["Trung bình", "Khá", "Tốt", "Cao cấp"],
    "House_Condition": ["Xuống cấp", "Cần sửa chữa", "Tốt", "Mới"],
    "Location_Type": ["Ngoại thành", "Ven trung tâm", "Trung tâm"],
    "Legal_Status": ["Đang chờ giấy tờ", "Hợp đồng mua bán", "Sổ đỏ/Sổ hồng"]
}
