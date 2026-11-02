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
from data import load_clean_data, load_listing_data, get_trained_models, _normalize_province


def predict_house_price(
    land_area: float,
    province: str = "Hà Nội",
    floor_area: float = None,
    bedrooms: int = 3,
    bathrooms: float = 2.0,
    floors: float = 2.0,
    house_age: float = 5.0,
    frontage: float = 4.0,
    road_width: float = 6.0,
    distance_to_center: float = 5.0,
    distance_to_school: float = 1.5,
    distance_to_hospital: float = 2.0,
    distance_to_market: float = 1.0,
    property_type: str = "Nhà phố",
    location_type: str = "Ven trung tâm",
) -> dict:
    """
    Dự đoán giá bán căn nhà (Tỷ VNĐ) tại thị trường Việt Nam bằng mô hình Random Forest đã kiểm định.
    """
    try:
        reg_model, _, _, _, _, _ = get_trained_models()
        df_clean = load_clean_data()

        # Mặc định floor_area = land_area * floors nếu không cung cấp
        if floor_area is None:
            floor_area = land_area * floors

        # Chuẩn hóa tên tỉnh (tìm kiếm gần đúng)
        all_provinces = df_clean["Province"].unique().tolist()
        matched_province = None
        for p in all_provinces:
            if p.lower() == str(province).strip().lower():
                matched_province = p
                break
        if not matched_province:
            for p in all_provinces:
                if str(province).strip().lower() in p.lower() or p.lower() in str(province).strip().lower():
                    matched_province = p
                    break
        if not matched_province:
            matched_province = "Hà Nội"  # Mặc định

        # Chuẩn hóa property_type
        all_ptypes = df_clean["Property_Type"].unique().tolist()
        matched_ptype = property_type if property_type in all_ptypes else all_ptypes[0]

        # Chuẩn hóa location_type
        all_ltypes = df_clean["Location_Type"].unique().tolist()
        matched_ltype = location_type if location_type in all_ltypes else all_ltypes[0]

        # Tạo DataFrame đầu vào đúng format
        input_data = pd.DataFrame(
            [
                {
                    "Land_Area": float(land_area),
                    "Floor_Area": float(floor_area),
                    "Floors": float(floors),
                    "Bedrooms": int(bedrooms),
                    "Bathrooms": float(bathrooms),
                    "House_Age": float(house_age),
                    "Frontage": float(frontage),
                    "Road_Width": float(road_width),
                    "Distance_To_Center": float(distance_to_center),
                    "Distance_To_School": float(distance_to_school),
                    "Distance_To_Hospital": float(distance_to_hospital),
                    "Distance_To_Market": float(distance_to_market),
                    "Province": matched_province,
                    "Property_Type": matched_ptype,
                    "Location_Type": matched_ltype,
                }
            ]
        )

        pred_log = reg_model.predict(input_data)[0]
        estimated_price = float(np.expm1(pred_log))

        # Khoảng giá dao động (±12%)
        lower_bound = max(0.1, estimated_price * 0.88)
        upper_bound = estimated_price * 1.12
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
                "property_type": matched_ptype,
                "distance_to_center_km": distance_to_center,
            },
            "note": "Giá được ước tính bằng mô hình Random Forest Regressor đã kiểm định (dữ liệu nhà ở Việt Nam).",
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
            target = str(province).strip().lower()
            prov_df = df[df["Province"].str.lower() == target]

            if prov_df.empty:
                # Thử tìm kiếm mờ
                matched = [p for p in df["Province"].unique() if target in p.lower() or p.lower() in target]
                if matched:
                    prov_df = df[df["Province"] == matched[0]]
                    province = matched[0]
                else:
                    return {
                        "status": "not_found",
                        "message": f"Không tìm thấy tỉnh/thành '{province}' trong bộ dữ liệu.",
                        "available_provinces_sample": sorted(df["Province"].unique())[:10],
                    }

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


def segment_house(price_billion_vnd: float, land_area_m2: float = 80.0) -> dict:
    """
    Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp / Hạng sang)
    dựa trên thuật toán K-Means (k=4) — phù hợp với thị trường Việt Nam.
    """
    try:
        _, (kmeans, mapping), km_scaler, _, _, _ = get_trained_models()

        log_input = pd.DataFrame(
            [[np.log1p(float(price_billion_vnd)), np.log1p(float(land_area_m2))]],
            columns=["Price_Billion_VND", "Land_Area"],
        )
        scaled_input = km_scaler.transform(log_input)
        raw_cluster = kmeans.predict(scaled_input)[0]
        mapped_segment = mapping[raw_cluster]

        segment_names = {
            0: "Bình dân (Starter)",
            1: "Trung cấp (Mid-tier)",
            2: "Cao cấp (Premium)",
            3: "Hạng sang (Luxury)",
        }
        segment_desc = {
            0: "Mức giá dưới 2 tỷ VNĐ. Phù hợp cho người mua nhà lần đầu, nhà ở xã hội hoặc khu vực ngoại tỉnh.",
            1: "Mức giá từ 2–5 tỷ VNĐ. Phân khúc nhà ở gia đình phổ biến nhất tại các tỉnh/thành loại 2.",
            2: "Mức giá từ 5–15 tỷ VNĐ. Nhà phố, chung cư cao cấp tại các đô thị lớn (Hà Nội, TP.HCM, Đà Nẵng).",
            3: "Mức giá trên 15 tỷ VNĐ. Biệt thự, penthouse, dự án cao cấp như Vinhomes, Sun Group.",
        }

        return {
            "status": "success",
            "segment_id": int(mapped_segment),
            "segment_name": segment_names[mapped_segment],
            "price_analyzed": f"{float(price_billion_vnd):.2f} tỷ VNĐ",
            "area_analyzed": f"{float(land_area_m2):.0f} m²",
            "market_profile": segment_desc[mapped_segment],
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi phân khúc: {str(e)}"}


def find_similar_houses(
    province: str = None,
    target_price_billion: float = None,
    bedrooms: int = None,
    land_area_m2: float = None,
    max_results: int = 3,
) -> dict:
    """
    Tìm kiếm các căn nhà thực tế có cấu trúc và mức giá tương đồng.
    Nguồn: house_cleaned.csv (30,078 dòng) — chứa địa chỉ thật, tên dự án Vinhomes thật.
    """
    try:
        # Dùng listing data thực tế (house_cleaned.csv) thay vì ML data
        df = load_listing_data()
        filtered = df.copy()

        # Lọc theo tỉnh/thành nếu có (chuẩn hóa tên để cross-file match đúng)
        if province and str(province).strip().lower() not in ["all", "any", "tùy ý", ""]:
            norm_input = _normalize_province(str(province).strip())
            matched_prov = None
            for p in df["Province_norm"].unique():
                if norm_input.lower() in p.lower() or p.lower() in norm_input.lower():
                    matched_prov = p
                    break
            if matched_prov:
                filtered = filtered[filtered["Province_norm"] == matched_prov]

        # Lọc theo số phòng ngủ nếu có
        if bedrooms is not None and bedrooms > 0:
            filtered = filtered[(filtered["Bedrooms"] >= bedrooms - 1) & (filtered["Bedrooms"] <= bedrooms + 1)]

        # Nới lỏng nếu quá ít kết quả
        if len(filtered) < max_results:
            filtered = df.copy()

        # Tính khoảng cách tương đồng (Euclidean trên giá và diện tích chuẩn hóa)
        ref_price = float(target_price_billion) if target_price_billion else df["Price_Billion_VND"].median()
        ref_area = float(land_area_m2) if land_area_m2 else df["Land_Area"].median()

        price_std = df["Price_Billion_VND"].std()
        area_std = df["Land_Area"].std()

        diff_score = np.sqrt(
            ((filtered["Price_Billion_VND"] - ref_price) / price_std) ** 2
            + ((filtered["Land_Area"] - ref_area) / area_std) ** 2
        )

        similar_indices = diff_score.sort_values().head(max_results).index
        similar_houses = filtered.loc[similar_indices]

        results = []
        for _, row in similar_houses.iterrows():
            # Hiển thị tên dự án nếu có, ngược lại dùng địa chỉ đầy đủ
            project = str(row.get("Project", "Unknown"))
            display_name = project if project not in ("Unknown", "", "nan") else str(row.get("Full_Address", ""))

            results.append(
                {
                    "display_name": display_name,
                    "full_address": str(row.get("Full_Address", "")),
                    "project": project if project not in ("Unknown", "", "nan") else "",
                    "province": row["Province"],
                    "district": str(row.get("District", "")),
                    "ward": str(row.get("Ward", "")),
                    "street": str(row.get("Street", "")) if str(row.get("Street", "")) != "Unknown" else "",
                    "price_formatted": f"{row['Price_Billion_VND']:.2f} tỷ VNĐ",
                    "price_per_m2": f"{row['price_per_m2']:.1f} triệu/m²",
                    "price_segment": str(row.get("Price_Segment", "")),
                    "land_area_m2": round(float(row["Land_Area"]), 1),
                    "bedrooms": int(row["Bedrooms"]),
                    "bathrooms": float(row["Bathrooms"]),
                    "floors": int(row.get("Floors", 1)),
                    "legal_status": str(row.get("Legal_Status", "")),
                    "furniture_state": str(row.get("Furniture_State", "")),
                }
            )

        return {
            "status": "success",
            "count": len(results),
            "data_source": "house_cleaned.csv (30,078 listings thực tế)",
            "search_criteria": {
                "province": province or "Toàn quốc",
                "target_price": f"{ref_price:.2f} tỷ VNĐ" if target_price_billion else "Mặc định trung vị",
                "land_area_m2": f"{ref_area:.0f} m²" if land_area_m2 else "Mặc định trung vị",
            },
            "matches": results,
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi tìm kiếm: {str(e)}"}



def explain_price_factors() -> dict:
    """
    Giải thích các yếu tố tác động mạnh nhất đến giá trị nhà ở Việt Nam (Feature Importance từ Random Forest).
    """
    try:
        _, _, _, _, _, feat_imp = get_trained_models()

        top_10 = feat_imp.head(10).round(4).to_dict()
        insights = [
            "1. Vị trí địa lý (Province) và loại vị trí (trung tâm/ngoại thành) là yếu tố chi phối mạnh nhất — nhà cùng diện tích tại Hà Nội có thể gấp 3–5 lần tỉnh lẻ.",
            "2. Diện tích đất (Land_Area) và diện tích sàn (Floor_Area) ảnh hưởng trực tiếp đến giá tuyệt đối — mỗi m² bổ sung đẩy giá lên đáng kể ở đô thị lớn.",
            "3. Khoảng cách đến trung tâm (Distance_To_Center) tỷ lệ nghịch với giá: càng xa trung tâm giá càng giảm, đặc biệt rõ tại TP.HCM và Hà Nội.",
            "4. Số tầng, mặt tiền (Frontage) và độ rộng đường (Road_Width) đóng vai trò quan trọng đối với nhà phố thương mại.",
            "5. Tình trạng pháp lý (Legal_Status: Sổ đỏ/Sổ hồng) ảnh hưởng đáng kể đến thanh khoản và giá trị thị trường của bất động sản.",
        ]

        return {
            "status": "success",
            "top_factors_importance_share": top_10,
            "key_market_takeaways": insights,
            "methodology": "Phân tích trích xuất từ mô hình Random Forest Regressor (100 cây quyết định) trên dữ liệu nhà ở Việt Nam sạch.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi giải thích: {str(e)}"}


# Danh mục ánh xạ Tool dùng cho LLM Function Calling
TOOL_CATALOG = {
    "predict_house_price": predict_house_price,
    "get_market_statistics": get_market_statistics,
    "segment_house": segment_house,
    "find_similar_houses": find_similar_houses,
    "explain_price_factors": explain_price_factors,
}
