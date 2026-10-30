# Phân Hệ Xử Lý & Khám Phá Dữ Liệu Bất Động Sản Việt Nam
**Tác giả (Thực hiện):** Bách (`feat/bach-ai`)  
**Môn học:** Data Manipulation & Visualization / Machine Learning  
**Dự án:** AI_PROJECT_TEAM  

---

## 1. Tổng Quan Phân Hệ
Phân hệ này đảm nhiệm toàn bộ quy trình tiền xử lý, làm sạch và phân tích khám phá dữ liệu (EDA) cho bài toán định giá và phân tích bất động sản Việt Nam:
1. **Làm sạch dữ liệu chuẩn mực (Data Cleaning Pipeline)**: Loại bỏ triệt để các ô khuyết (`NaN/Null`), lỗi gõ số sai lệch (`Typo`), xung đột logic và chuẩn hóa mã hóa ký tự `UTF-8-SIG`.
2. **Khám phá dữ liệu (Exploratory Data Analysis - EDA)**: Trực quan hóa 9 chiều phân tích thống kê cốt lõi từ ma trận tương quan, phân phối giá, khoảng cách đô thị đến giá trung vị 63 tỉnh thành.
3. **Báo cáo kỹ thuật chi tiết**: File báo cáo Word hoàn chỉnh (`Bao_Cao_Quy_Trinh_Lam_Sach_Du_Lieu.docx`) đối chiếu chi tiết chất lượng dữ liệu trước và sau khi làm sạch.

---

## 2. Cấu Trúc Thư Mục
```
vietnam_housing_data/
├── 01_clean_data.py                    # Script pipeline làm sạch dữ liệu
├── 02_eda.py                           # Script trực quan hóa 9 biểu đồ EDA
├── common.py                           # Cấu hình danh mục thuộc tính & đường dẫn
├── clean.py                            # Script tiền xử lý dữ liệu (bản đối soát 30k dòng)
├── Bao_Cao_Quy_Trinh_Lam_Sach_Du_Lieu.docx # Báo cáo kỹ thuật quy trình làm sạch
├── README.md                           # Hướng dẫn sử dụng module
├── data/
│   ├── Vietnam_Housing_Data_10000.xlsx       # Tệp dữ liệu thô gốc (10,000 dòng)
│   ├── housing_clean.csv                     # Tệp dữ liệu sạch chuẩn (9,714 dòng, 0 Null)
│   └── Vietnam_Housing_Data_10000_clean.xlsx # Tệp Excel chuẩn đã làm sạch
└── eda_charts/                         # 9 Biểu đồ phân tích chất lượng cao
    ├── 01_missing_values.png
    ├── 02_price_histograms.png
    ├── 03_correlation_with_log_price.png
    ├── 04_land_area_vs_price.png
    ├── 05_price_by_property_type.png
    ├── 06_price_by_location_type.png
    ├── 07_distance_vs_price_per_m2.png
    ├── 08_median_price_by_province.png
    └── 09_correlation_heatmap.png
```

---

## 3. Hướng Dẫn Chạy & Tái Lập Kết Quả

### Bước 1: Chạy làm sạch dữ liệu
Từ thư mục gốc dự án hoặc bên trong thư mục này:
```bash
python vietnam_housing_data/01_clean_data.py
```
*Kết quả:* Dữ liệu thô từ `Vietnam_Housing_Data_10000.xlsx` được xử lý và xuất ra `data/housing_clean.csv` và `data/Vietnam_Housing_Data_10000_clean.xlsx` (sạch 100%, 0 giá trị khuyết).

### Bước 2: Chạy trực quan hóa biểu đồ EDA
```bash
python vietnam_housing_data/02_eda.py
```
*Kết quả:* Tự động xuất 9 biểu đồ PNG sắc nét vào thư mục `eda_charts/`.
