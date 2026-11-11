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
from data import load_clean_data, load_listing_data, get_trained_models


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

        # 1. Chuẩn hóa tên tỉnh/thành
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
            matched_province = "Hà Nội"

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

        # Xử lý biến phân loại và số nguyên (Mode)
        property_type = property_type if property_type else prov_df["Property_Type"].mode()[0]
        location_type = location_type if location_type else prov_df["Location_Type"].mode()[0]
        bedrooms = int(get_val(bedrooms, "Bedrooms", is_mode=True))
        floors = float(get_val(floors, "Floors", is_mode=True))
        bathrooms = float(get_val(bathrooms, "Bathrooms", is_mode=True))

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
                "property_type": property_type,
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


def segment_house(price_billion_vnd: float, land_area_m2: float, province: str) -> dict:
    """
    Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp / Hạng sang)
    dựa trên thuật toán K-Means (k=4) bằng phân cụm cục bộ (Local Clustering).
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    try:
        df = load_clean_data()
        
        # 1. Lọc tập dữ liệu theo tỉnh thành
        df_local = df[df['Province'].str.contains(province, case=False, na=False)].copy()
        
        # Fallback: Nếu tỉnh lạ hoặc quá ít dữ liệu, lấy dữ liệu toàn quốc
        if len(df_local) < 15:
            df_local = df.copy()
            province_analyzed = "Toàn quốc (Mặc định)"
        else:
            province_analyzed = df_local['Province'].iloc[0]

        # 2. Tiền xử lý
        X_local = df_local[['Price_Billion_VND', 'Land_Area']].copy()
        X_log = np.log1p(X_local)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_log)
        
        # 3. K-Means
        kmeans = KMeans(n_clusters=4, n_init=15, random_state=42)
        df_local['Raw_Cluster'] = kmeans.fit_predict(X_scaled)
        
        # 4. Gom nhãn theo thứ bậc giá
        cluster_prices = df_local.groupby('Raw_Cluster')['Price_Billion_VND'].mean().sort_values()
        cluster_mapping = {old: new for new, old in enumerate(cluster_prices.index)}
        
        # 5. Phân loại căn nhà đầu vào
        input_data = pd.DataFrame([[np.log1p(float(price_billion_vnd)), np.log1p(float(land_area_m2))]],
                                  columns=['Price_Billion_VND', 'Land_Area'])
        input_scaled = scaler.transform(input_data)
        raw_pred = kmeans.predict(input_scaled)[0]
        final_segment = cluster_mapping[raw_pred]

        segment_names = {
            0: "Bình dân (Starter)",
            1: "Trung cấp (Mid-tier)",
            2: "Cao cấp (Premium)",
            3: "Hạng sang (Luxury)"
        }
        
        segment_desc = {
            0: f"Mức giá rẻ nhất tại {province_analyzed}. Phù hợp cho nhà ở xã hội, ngõ nhỏ.",
            1: f"Phân khúc phổ biến nhất tại {province_analyzed}. Nhà ở gia đình trung lưu.",
            2: f"Phân khúc giá cao tại {province_analyzed}. Chung cư cao cấp, nhà mặt phố nhỏ.",
            3: f"Mức giá đắt đỏ nhất tại {province_analyzed}. Biệt thự, dự án hạng sang."
        }

        return {
            "status": "success",
            "province_analyzed": province_analyzed,
            "segment_name": segment_names[final_segment],
            "price_analyzed": f"{float(price_billion_vnd):.2f} tỷ VNĐ",
            "area_analyzed": f"{float(land_area_m2):.0f} m²",
            "market_profile": segment_desc[final_segment],
            "local_average_price_for_segment": f"{cluster_prices.iloc[final_segment]:.2f} tỷ VNĐ"
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi phân khúc: {str(e)}"}


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
        mask = df_listing['Province'].str.contains(province, case=False, na=False)
        df_filtered = df_listing[mask].copy()
        
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
            address = f"{house.get('Street', '')}, {house.get('Ward', '')}, {house.get('District', '')}, {house['Province']}".replace(" ,", "")
            
            results.append({
                "Mã nhà": str(house.get("House_ID", f"ID_{i}")),
                "Loại nhà": str(house.get("Property_Type", house.get("Type", "Nhà đất"))),
                "Giá bán (Tỷ)": round(float(house["Price_Billion_VND"]), 2),
                "Diện tích (m2)": round(float(house["Land_Area"]), 1),
                "Phòng ngủ": int(house["Bedrooms"]),
                "Địa chỉ": address.strip(", "),
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
