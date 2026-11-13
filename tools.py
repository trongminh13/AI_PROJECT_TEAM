"""
Module: tools.py
Triển khai 5 công cụ nghiệp vụ bất động sản chuẩn hóa cho thị trường Việt Nam:
1. predict_house_price: Dự đoán giá bán bằng mô hình Random Forest Regressor (Tỷ VNĐ)
2. get_market_statistics: Thống kê số liệu thị trường theo tỉnh/thành hoặc toàn quốc
3. segment_house: Phân khúc nhà (Bình dân, Trung cấp, Cao cấp, Hạng sang) bằng K-Means
4. find_similar_houses: Tìm kiếm các căn nhà thực tế tương đồng nhất trong kho dữ liệu
5. explain_price_factors: Cung cấp mức độ quan trọng (Feature Importance) và giải thích yếu tố định giá
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from data import (
    load_clean_data, load_listing_data, get_trained_models, get_model_report,
    match_province, classify_segment, segment_table, SEGMENT_BINS, FEATURE_LABELS,
)


def predict_house_price(
    land_area: float,
    province: str,
    floor_area: float = None,
    bedrooms: int = None,
    bathrooms: float = None,
    floors: float = None,
    house_age: float = None,
    frontage: float = None,
    road_width: float = None,
    distance_to_center: float = None,
    distance_to_school: float = None,
    distance_to_hospital: float = None,
    distance_to_market: float = None,
    property_type: str = None,
    location_type: str = None,
) -> dict:
    """
    Dự đoán giá bán căn nhà (Tỷ VNĐ).
    Các tham số bị thiếu sẽ được TỰ ĐỘNG ĐIỀN bằng giá trị Mode/Median của tỉnh/thành đó.
    """
    try:
        reg_model, _, _, _, _, _ = get_trained_models()
        df_clean = load_clean_data()

        # 1. Chuẩn hóa tên tỉnh/thành (KHÔNG âm thầm đổi sang Hà Nội nữa)
        all_provinces = df_clean["Province"].unique().tolist()
        matched_province = match_province(province, all_provinces)
        if not matched_province:
            return {
                "status": "error",
                "message": f"Không nhận diện được tỉnh/thành '{province}'. Hãy hỏi lại khách để chọn một tỉnh/thành hợp lệ.",
                "available_provinces": sorted(all_provinces),
            }

        # 2. Lọc Data theo Tỉnh để lấy hệ quy chiếu địa phương
        prov_df = df_clean[df_clean["Province"] == matched_province]
        if prov_df.empty:
            prov_df = df_clean # Fallback toàn quốc nếu lỗi

        # 3. TỰ ĐỘNG ĐIỀN KHUYẾT (DYNAMIC DEFAULTS)
        # Nguyên tắc: Dùng Mode cho số nguyên/phân loại, Dùng Median cho số thực/khoảng cách
        def get_val(val, col, is_mode=False):
            if val is not None:
                return val
            return prov_df[col].mode()[0] if is_mode else prov_df[col].median()

        # Xử lý biến phân loại: khớp không phân biệt hoa thường; sai giá trị thì dùng Mode và báo cảnh báo
        warnings_list = []

        def pick_category(value, col):
            valid = df_clean[col].unique().tolist()
            if value:
                hit = next((v for v in valid if v.lower() == str(value).strip().lower()), None)
                if hit:
                    return hit
                warnings_list.append(f"'{value}' không hợp lệ cho {col}; dùng giá trị phổ biến nhất tại {matched_province}. Hợp lệ: {valid}")
            return prov_df[col].mode()[0]

        property_type = pick_category(property_type, "Property_Type")
        location_type = pick_category(location_type, "Location_Type")
        # Số phòng ngủ / số tầng tương quan mạnh (r ~ 0,8) và Mode bị lệch do dữ liệu chặn trần ở 9 PN -> dùng Trung vị
        bedrooms = int(round(float(get_val(bedrooms, "Bedrooms"))))
        floors = float(round(float(get_val(floors, "Floors"))))
        if bathrooms is None:
            # Phòng tắm mặc định bám theo số phòng ngủ (cùng tỉnh); không đủ mẫu thì dùng Mode của tỉnh
            same_beds = prov_df.loc[prov_df["Bedrooms"] == bedrooms, "Bathrooms"]
            bathrooms = float(same_beds.median()) if len(same_beds) >= 10 else float(prov_df["Bathrooms"].mode()[0])
        bathrooms = float(bathrooms)

        # Xử lý biến liên tục, khoảng cách (Median)
        distance_to_center = float(get_val(distance_to_center, "Distance_To_Center"))
        distance_to_school = float(get_val(distance_to_school, "Distance_To_School"))
        distance_to_hospital = float(get_val(distance_to_hospital, "Distance_To_Hospital"))
        distance_to_market = float(get_val(distance_to_market, "Distance_To_Market"))
        house_age = float(get_val(house_age, "House_Age"))
        frontage = float(get_val(frontage, "Frontage"))
        road_width = float(get_val(road_width, "Road_Width"))

        # Diện tích sàn
        if floor_area is None:
            floor_area = float(land_area) * floors

        # 4. Tạo DataFrame đầu vào
        input_data = pd.DataFrame(
            [
                {
                    "Land_Area": float(land_area),
                    "Floor_Area": float(floor_area),
                    "Floors": floors,
                    "Bedrooms": bedrooms,
                    "Bathrooms": bathrooms,
                    "House_Age": house_age,
                    "Frontage": frontage,
                    "Road_Width": road_width,
                    "Distance_To_Center": distance_to_center,
                    "Distance_To_School": distance_to_school,
                    "Distance_To_Hospital": distance_to_hospital,
                    "Distance_To_Market": distance_to_market,
                    "Province": matched_province,
                    "Property_Type": property_type,
                    "Location_Type": location_type,
                }
            ]
        )

        pred_log = reg_model.predict(input_data)[0]
        estimated_price = float(np.expm1(pred_log))

        # Khoảng giá 80%: phân vị 10-90 của sai số trên tập kiểm tra (thay cho ±12% cố định)
        report = get_model_report()
        lower_bound = float(np.expm1(pred_log + report["q10"]))
        upper_bound = float(np.expm1(pred_log + report["q90"]))
        price_per_m2 = (estimated_price * 1000) / float(land_area) if land_area > 0 else 0.0  # Triệu/m²

        return {
            "status": "success",
            "estimated_price_billion_vnd": round(estimated_price, 3),
            "estimated_price_formatted": f"{estimated_price:.2f} tỷ VNĐ",
            "price_range_formatted": f"{lower_bound:.2f} - {upper_bound:.2f} tỷ VNĐ",
            "price_per_m2_million": round(price_per_m2, 1),
            "price_per_m2_formatted": f"{price_per_m2:.1f} triệu/m²",
            "input_summary": {
                "province": matched_province,
                "land_area_m2": land_area,
                "floor_area_m2": floor_area,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "property_type": property_type,
                "distance_to_center_km": distance_to_center,
            },
            "model_quality": {
                "r2_on_log_price": round(report["r2_log"], 3),
                "mape_percent": round(report["mape_pct"], 1),
            },
            "warnings": warnings_list,
            "note": (
                f"Ước tính bằng Random Forest. Khoảng giá bao phủ khoảng 80% trường hợp trên tập kiểm tra; "
                f"sai số trung bình khoảng {report['mape_pct']:.0f}%, nên chỉ dùng để tham khảo."
            ),
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi dự đoán giá: {str(e)}"}


def get_market_statistics(province: str = None) -> dict:
    """
    Thống kê và phân tích thị trường bất động sản Việt Nam hoặc theo từng tỉnh/thành cụ thể.
    """
    try:
        df = load_clean_data()

        if province and str(province).strip().lower() not in ["all", "none", "toàn quốc", ""]:
            matched = match_province(province, df["Province"].unique().tolist())
            if not matched:
                return {
                    "status": "not_found",
                    "message": f"Không tìm thấy tỉnh/thành '{province}' trong bộ dữ liệu.",
                    "available_provinces": sorted(df["Province"].unique()),
                }
            province = matched
            prov_df = df[df["Province"] == matched]

            total = len(prov_df)
            mean_price = prov_df["Price_Billion_VND"].mean()
            median_price = prov_df["Price_Billion_VND"].median()
            min_price = prov_df["Price_Billion_VND"].min()
            max_price = prov_df["Price_Billion_VND"].max()
            avg_area = prov_df["Land_Area"].mean()
            avg_price_m2 = prov_df["price_per_m2"].mean()

            return {
                "status": "success",
                "scope": f"Tỉnh/Thành phố: {province}",
                "total_listings": int(total),
                "median_price_formatted": f"{median_price:.2f} tỷ VNĐ",
                "mean_price_formatted": f"{mean_price:.2f} tỷ VNĐ",
                "min_price_formatted": f"{min_price:.2f} tỷ VNĐ",
                "max_price_formatted": f"{max_price:.2f} tỷ VNĐ",
                "avg_land_area_m2": round(avg_area, 1),
                "avg_price_per_m2": f"{avg_price_m2:.1f} triệu/m²",
            }
        else:
            # Thống kê toàn quốc
            total = len(df)
            median_price = df["Price_Billion_VND"].median()
            mean_price = df["Price_Billion_VND"].mean()
            top_expensive = (
                df.groupby("Province")["Price_Billion_VND"]
                .median()
                .sort_values(ascending=False)
                .head(5)
                .apply(lambda x: f"{x:.2f} tỷ VNĐ")
                .to_dict()
            )
            top_affordable = (
                df.groupby("Province")["Price_Billion_VND"]
                .median()
                .sort_values(ascending=True)
                .head(5)
                .apply(lambda x: f"{x:.2f} tỷ VNĐ")
                .to_dict()
            )

            return {
                "status": "success",
                "scope": "Toàn quốc (Việt Nam)",
                "total_listings": int(total),
                "median_price_formatted": f"{median_price:.2f} tỷ VNĐ",
                "mean_price_formatted": f"{mean_price:.2f} tỷ VNĐ",
                "min_price_formatted": f"{df['Price_Billion_VND'].min():.2f} tỷ VNĐ",
                "max_price_formatted": f"{df['Price_Billion_VND'].max():.2f} tỷ VNĐ",
                "avg_land_area_m2": round(df["Land_Area"].mean(), 1),
                "avg_price_per_m2": f"{df['price_per_m2'].mean():.1f} triệu/m²",
                "top_5_expensive_provinces": top_expensive,
                "top_5_affordable_provinces": top_affordable,
            }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi thống kê: {str(e)}"}


def segment_house(price_billion_vnd: float, province: str = None, land_area_m2: float = None) -> dict:
    """
    Xác định phân khúc căn nhà theo NGƯỠNG GIÁ chung toàn quốc (dưới 2, 2-5, 5-15, trên 15 tỷ),
    kèm vị trí phần trăm của giá trong tỉnh/thành (nếu có) để so sánh với thị trường địa phương.
    """
    try:
        df = load_clean_data()
        price = float(price_billion_vnd)
        segment = classify_segment(price)
        info = next(s for s in segment_table() if s["name"] == segment)

        result = {
            "status": "success",
            "segment_name": segment,
            "price_analyzed": f"{price:.2f} tỷ VNĐ",
            "area_analyzed": f"{float(land_area_m2):.0f} m²" if land_area_m2 else "Không cung cấp",
            "definition": "Phân khúc theo ngưỡng giá: Bình dân < 2 tỷ; Trung cấp 2-5 tỷ; Cao cấp 5-15 tỷ; Hạng sang > 15 tỷ.",
            "market_profile": (
                f"Phân khúc {segment} chiếm {info['share_pct']}% số tin toàn quốc; giá trung vị {info['median_price']} tỷ, "
                f"diện tích đất trung bình {info['mean_land_area']:.0f} m², loại nhà phổ biến nhất: "
                f"{info['top_property_type']} ({info['top_property_share_pct']:.0f}%)."
            ),
        }
        matched = match_province(province, df["Province"].unique().tolist()) if province else None
        if matched:
            prices = df.loc[df["Province"] == matched, "Price_Billion_VND"]
            pct = float((prices < price).mean() * 100)
            result["province_analyzed"] = matched
            result["local_position"] = (
                f"Mức giá {price:.2f} tỷ cao hơn {pct:.0f}% số tin tại {matched} (trung vị địa phương {prices.median():.2f} tỷ)."
            )
        return result
    except Exception as e:
        return {"status": "error", "message": f"Lỗi phân khúc: {str(e)}"}


def explain_market_segments() -> dict:
    """Mô tả 4 phân khúc thị trường bằng số liệu thật từ dữ liệu (không dùng văn bản cứng)."""
    try:
        return {
            "status": "success",
            "definition": "Phân khúc theo ngưỡng giá: Bình dân < 2 tỷ; Trung cấp 2-5 tỷ; Cao cấp 5-15 tỷ; Hạng sang > 15 tỷ.",
            "segments": segment_table(),
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi mô tả phân khúc: {str(e)}"}


def find_similar_houses(
    price_billion: float,
    land_area: float,
    province: str,
    bedrooms: int = None,
    property_type: str = None,
    limit: int = 3
) -> dict:
    """
    Tìm kiếm các căn nhà tương đồng trong kho hàng thực tế (9,714 dòng)...
    Sử dụng kết hợp Lọc cứng (Tỉnh/Thành, Loại nhà) và KNN trên 3 đặc trưng (Giá, Diện tích, Phòng ngủ).
    """
    try:
        # 1. Tải dữ liệu kho hàng thực tế và công cụ chuẩn hóa
        df_listing = load_listing_data()
        
        # Lấy nn_scaler từ data.py (biến thứ 5 trong tuple trả về)
        _, _, _, _, nn_scaler, _ = get_trained_models() 
        
        # 2. BỘ LỌC CỨNG (Hard Pre-filtering)
        # Lọc kho hàng theo Tỉnh/Thành phố (Không phân biệt hoa thường)
        matched = match_province(province, df_listing["Province"].unique().tolist())
        df_filtered = df_listing[df_listing["Province"] == matched].copy() if matched else df_listing.iloc[0:0]
        
        if df_filtered.empty:
            return {
                "status": "error", 
                "message": f"Hiện tại không có dữ liệu nhà đất nào tại: {province}"
            }
            
        # Lọc thêm theo Loại nhà (Nếu AI/Người dùng có cung cấp)
        if property_type and 'Property_Type' in df_filtered.columns:
            prop_mask = df_filtered['Property_Type'].str.contains(property_type, case=False, na=False)
            if not df_filtered[prop_mask].empty:
                df_filtered = df_filtered[prop_mask]
                
        # 3. TỰ ĐỘNG NỘI SUY (Dynamic Default cho Phòng ngủ)
        if bedrooms is None:
            # Lấy trung vị số phòng ngủ của chính khu vực và loại nhà đó
            bedrooms = int(df_filtered['Bedrooms'].median())
            if pd.isna(bedrooms): 
                bedrooms = 3 # Dự phòng an toàn

        # 4. CHẠY KNN CỤC BỘ (Trên tập dữ liệu đã lọc)
        # Trích xuất đúng 3 đặc trưng cốt lõi
        X_raw = df_filtered[["Price_Billion_VND", "Land_Area", "Bedrooms"]]
        
        # Áp dụng Logarit và Chuẩn hóa (Dùng lại tỷ lệ chuẩn của toàn quốc)
        X_scaled = nn_scaler.transform(np.log1p(X_raw))
        
        # Khởi tạo thuật toán đo khoảng cách (chạy cực nhanh vì tập dữ liệu đã thu hẹp)
        n_neighbors = min(limit, len(df_filtered))
        local_nn = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
        local_nn.fit(X_scaled)
        
        # 5. TẠO ĐIỂM MỤC TIÊU VÀ TÌM KIẾM
        target_raw = pd.DataFrame([{
            "Price_Billion_VND": float(price_billion),
            "Land_Area": float(land_area),
            "Bedrooms": float(bedrooms)
        }])
        target_scaled = nn_scaler.transform(np.log1p(target_raw))
        
        # Tính toán và lấy ra top n_neighbors căn nhà gần nhất
        distances, indices = local_nn.kneighbors(target_scaled)
        
        # 6. ĐÓNG GÓI KẾT QUẢ GỬI VỀ CHO AI AGENT
        results = []
        for i, idx in enumerate(indices[0]):
            house = df_filtered.iloc[idx]
            
            # Cấu trúc địa chỉ thực tế đẹp mắt
            address = ", ".join(str(x) for x in [house.get("Street"), house.get("Ward"), house.get("District"), house["Province"]] if pd.notna(x) and str(x).strip())

            results.append({
                "Mã nhà": str(house.get("House_ID", f"ID_{i}")),
                "Loại nhà": str(house.get("Property_Type", house.get("Type", "Nhà đất"))),
                "Giá bán (Tỷ)": round(float(house["Price_Billion_VND"]), 2),
                "Diện tích (m2)": round(float(house["Land_Area"]), 1),
                "Phòng ngủ": int(house["Bedrooms"]),
                "Địa chỉ": address,
                "Độ sai lệch": round(float(distances[0][i]), 4) # Càng gần 0 càng giống
            })
            
        return {
            "status": "success",
            "search_criteria": {
                "province": province,
                "price_billion": price_billion,
                "land_area": land_area,
                "assumed_bedrooms": int(bedrooms)
            },
            "recommendations": results
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Lỗi hệ thống khi tìm kiếm: {str(e)}"}



def explain_price_factors() -> dict:
    """
    Giải thích các yếu tố tác động mạnh nhất đến giá nhà (Feature Importance đã gộp theo biến gốc)
    và các nhận xét được tính trực tiếp từ dữ liệu.
    """
    try:
        _, _, _, _, _, feat_imp = get_trained_models()
        df = load_clean_data()
        top = feat_imp.head(8)
        shares = {FEATURE_LABELS.get(k, k): round(float(v), 4) for k, v in top.items()}

        corr_land = float(df["Land_Area"].corr(df["log_price"]))
        corr_dist = float(df["Distance_To_Center"].corr(df["log_price"]))
        prov_med = df.groupby("Province")["Price_Billion_VND"].median().sort_values(ascending=False)
        best, worst = prov_med.index[0], prov_med.index[-1]
        insights = [
            f"1. Diện tích đất và tỉnh/thành là hai yếu tố mạnh nhất: {FEATURE_LABELS.get(top.index[0], top.index[0])} "
            f"({top.iloc[0]*100:.1f}%) và {FEATURE_LABELS.get(top.index[1], top.index[1])} ({top.iloc[1]*100:.1f}%).",
            f"2. Diện tích đất tương quan dương với log giá (r = {corr_land:.2f}).",
            f"3. Càng xa trung tâm giá càng giảm (r = {corr_dist:.2f} với log giá).",
            f"4. Giá trung vị cao nhất tại {best} ({prov_med.iloc[0]:.2f} tỷ), thấp nhất tại {worst} ({prov_med.iloc[-1]:.2f} tỷ), "
            f"gấp khoảng {prov_med.iloc[0]/prov_med.iloc[-1]:.1f} lần.",
        ]
        return {
            "status": "success",
            "top_factors_importance_share": shares,
            "key_market_takeaways": insights,
            "methodology": "Feature Importance của Random Forest (100 cây), đã gộp các cột one-hot về biến gốc.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi giải thích: {str(e)}"}

# Danh mục ánh xạ Tool dùng cho LLM Function Calling
TOOL_CATALOG = {
    "predict_house_price": predict_house_price,
    "get_market_statistics": get_market_statistics,
    "segment_house": segment_house,
    "explain_market_segments": explain_market_segments,
    "find_similar_houses": find_similar_houses,
    "explain_price_factors": explain_price_factors,
}
