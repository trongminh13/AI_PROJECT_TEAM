"""
Module: tools.py
Triển khai 5 công cụ nghiệp vụ bất động sản chuẩn hóa:
1. predict_house_price: Dự đoán giá bán bằng mô hình Random Forest Regressor
2. get_market_statistics: Thống kê số liệu thị trường theo thành phố hoặc toàn vùng King County
3. segment_house: Phân khúc nhà (Bình dân, Trung cấp, Cao cấp) bằng K-Means
4. find_similar_houses: Tìm kiếm các căn nhà thực tế tương đồng nhất trong kho dữ liệu
5. explain_price_factors: Cung cấp mức độ quan trọng (Feature Importance) và giải thích yếu tố định giá
"""

import numpy as np
import pandas as pd
from data import load_clean_data, get_trained_models


def predict_house_price(
    sqft_living: float,
    city: str = "Seattle",
    bedrooms: int = 3,
    bathrooms: float = 2.0,
    sqft_lot: float = 7500.0,
    floors: float = 1.5,
    waterfront: int = 0,
    view: int = 0,
    condition: int = 3,
    yr_built: int = 1975,
    has_basement: int = 0,
    is_renovated: int = 0,
) -> dict:
    """
    Dự đoán giá bán căn nhà dựa trên mô hình Random Forest đã được kiểm định 5-Fold CV.
    """
    try:
        reg_model, _, _, _, _, _ = get_trained_models()
        df_clean = load_clean_data()

        # Chuẩn hóa tên thành phố (tìm kiếm gần đúng)
        all_cities = df_clean["city"].unique().tolist()
        matched_city = None
        for c in all_cities:
            if c.lower() == str(city).strip().lower():
                matched_city = c
                break
        if not matched_city:
            # Fallback nếu tên thành phố viết hơi khác hoặc không có
            for c in all_cities:
                if str(city).strip().lower() in c.lower():
                    matched_city = c
                    break
        if not matched_city:
            matched_city = "Seattle"  # Mặc định

        # Tạo DataFrame đầu vào đúng format
        input_data = pd.DataFrame(
            [
                {
                    "bedrooms": int(bedrooms),
                    "bathrooms": float(bathrooms),
                    "sqft_living": float(sqft_living),
                    "log_sqft_lot": np.log1p(float(sqft_lot)),
                    "floors": float(floors),
                    "waterfront": int(waterfront),
                    "view": int(view),
                    "condition": int(condition),
                    "yr_built": int(yr_built),
                    "is_renovated": int(is_renovated),
                    "has_basement": int(has_basement),
                    "city": matched_city,
                }
            ]
        )

        pred_log = reg_model.predict(input_data)[0]
        estimated_price = float(np.expm1(pred_log))

        # Khoảng giá dao động theo MAE thực tế (~$98,000 hoặc 12%)
        lower_bound = max(50000.0, estimated_price * 0.90)
        upper_bound = estimated_price * 1.10
        price_per_sqft = estimated_price / float(sqft_living) if sqft_living > 0 else 0.0

        return {
            "status": "success",
            "estimated_price_usd": round(estimated_price, -2),
            "estimated_price_formatted": f"${estimated_price:,.0f} USD",
            "price_range_formatted": f"${lower_bound:,.0f} - ${upper_bound:,.0f} USD",
            "price_per_sqft_usd": round(price_per_sqft, 1),
            "input_summary": {
                "city": matched_city,
                "sqft_living": sqft_living,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "sqft_lot": sqft_lot,
                "yr_built": yr_built,
                "waterfront": "Có" if waterfront else "Không",
            },
            "note": "Giá được ước tính bằng mô hình Random Forest Regressor đã kiểm định 5-fold CV (R² ≈ 0.72).",
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi dự đoán giá: {str(e)}"}


def get_market_statistics(city: str = None) -> dict:
    """
    Thống kê và phân tích thị trường bất động sản King County hoặc theo từng thành phố cụ thể.
    """
    try:
        df = load_clean_data()

        if city and str(city).strip().lower() not in ["all", "none", "toàn vùng", ""]:
            target_city = str(city).strip().lower()
            city_df = df[df["city"].str.lower() == target_city]

            if city_df.empty:
                # Thử tìm kiếm mờ
                matched = [c for c in df["city"].unique() if target_city in c.lower()]
                if matched:
                    city_df = df[df["city"] == matched[0]]
                    city = matched[0]
                else:
                    return {
                        "status": "not_found",
                        "message": f"Không tìm thấy thành phố '{city}' trong bộ dữ liệu King County.",
                        "available_cities_sample": sorted(df["city"].unique())[:10],
                    }

            total_sales = len(city_df)
            mean_price = city_df["price"].mean()
            median_price = city_df["price"].median()
            min_price = city_df["price"].min()
            max_price = city_df["price"].max()
            avg_sqft = city_df["sqft_living"].mean()
            avg_price_sqft = (city_df["price"] / city_df["sqft_living"]).mean()

            return {
                "status": "success",
                "scope": f"Thành phố {city}",
                "total_transactions": int(total_sales),
                "median_price_formatted": f"${median_price:,.0f} USD",
                "mean_price_formatted": f"${mean_price:,.0f} USD",
                "min_price_formatted": f"${min_price:,.0f} USD",
                "max_price_formatted": f"${max_price:,.0f} USD",
                "avg_sqft_living": round(avg_sqft, 1),
                "avg_price_per_sqft": f"${avg_price_sqft:,.1f}/sqft",
            }
        else:
            # Thống kê toàn vùng
            total_sales = len(df)
            median_price = df["price"].median()
            mean_price = df["price"].mean()
            top_expensive_cities = (
                df.groupby("city")["price"]
                .median()
                .sort_values(ascending=False)
                .head(5)
                .apply(lambda x: f"${x:,.0f}")
                .to_dict()
            )
            top_affordable_cities = (
                df.groupby("city")["price"]
                .median()
                .sort_values(ascending=True)
                .head(5)
                .apply(lambda x: f"${x:,.0f}")
                .to_dict()
            )

            return {
                "status": "success",
                "scope": "Toàn vùng King County (Seattle & khu vực phụ cận)",
                "total_transactions": int(total_sales),
                "median_price_formatted": f"${median_price:,.0f} USD",
                "mean_price_formatted": f"${mean_price:,.0f} USD",
                "min_price_formatted": f"${df['price'].min():,.0f} USD",
                "max_price_formatted": f"${df['price'].max():,.0f} USD",
                "avg_sqft_living": round(df["sqft_living"].mean(), 1),
                "avg_price_per_sqft": f"${df['price_per_sqft'].mean():,.1f}/sqft",
                "top_5_expensive_cities_by_median": top_expensive_cities,
                "top_5_affordable_cities_by_median": top_affordable_cities,
            }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi thống kê: {str(e)}"}


def segment_house(price: float, sqft_living: float) -> dict:
    """
    Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp) dựa trên thuật toán K-Means (k=3).
    """
    try:
        _, (kmeans, mapping), km_scaler, _, _, _ = get_trained_models()

        log_input = pd.DataFrame(
            [[np.log1p(float(price)), np.log1p(float(sqft_living))]],
            columns=["price", "sqft_living"],
        )
        scaled_input = km_scaler.transform(log_input)
        raw_cluster = kmeans.predict(scaled_input)[0]
        mapped_segment = mapping[raw_cluster]

        segment_names = {
            0: "Bình dân (Starter / Affordable)",
            1: "Trung cấp (Mid-tier / Family)",
            2: "Cao cấp (Luxury / High-end)",
        }
        segment_desc = {
            0: "Mức giá trung bình ~ $330,000 USD, diện tích ~ 1,400 sqft. Phù hợp cho người mua nhà lần đầu hoặc gia đình nhỏ.",
            1: "Mức giá trung bình ~ $580,000 USD, diện tích ~ 2,300 sqft. Phân khúc nhà ở gia đình phổ biến nhất tại ngoại ô King County.",
            2: "Mức giá trung bình ~ $1,160,000 USD, diện tích ~ 3,700 sqft. Bất động sản cao cấp, view đẹp hoặc vị trí đắc địa (Medina, Bellevue, Mercer Island).",
        }

        return {
            "status": "success",
            "segment_id": int(mapped_segment),
            "segment_name": segment_names[mapped_segment],
            "price_analyzed": f"${float(price):,.0f} USD",
            "sqft_analyzed": f"{float(sqft_living):,.0f} sqft",
            "market_profile": segment_desc[mapped_segment],
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi phân khúc: {str(e)}"}


def find_similar_houses(
    city: str = None,
    target_price: float = None,
    bedrooms: int = None,
    sqft_living: float = None,
    max_results: int = 3,
) -> dict:
    """
    Tìm kiếm các căn nhà thực tế có cấu trúc và mức giá tương đồng trong tập dữ liệu 4,548 giao dịch.
    """
    try:
        df = load_clean_data()
        filtered = df.copy()

        # Lọc theo thành phố nếu có
        if city and str(city).strip().lower() not in ["all", "any", "tùy ý", ""]:
            matched_city = None
            for c in df["city"].unique():
                if str(city).strip().lower() in c.lower():
                    matched_city = c
                    break
            if matched_city:
                filtered = filtered[filtered["city"] == matched_city]

        # Lọc theo số phòng ngủ nếu có
        if bedrooms is not None and bedrooms > 0:
            filtered = filtered[(filtered["bedrooms"] >= bedrooms - 1) & (filtered["bedrooms"] <= bedrooms + 1)]

        # Nếu tập lọc còn quá ít, nới lỏng về tập ban đầu
        if len(filtered) < max_results:
            filtered = df.copy()

        # Tính khoảng cách tương đồng (Euclidean distance trên giá và diện tích đã chuẩn hóa)
        ref_price = float(target_price) if target_price else df["price"].median()
        ref_sqft = float(sqft_living) if sqft_living else df["sqft_living"].median()

        # Tính độ lệch tương đối
        price_std = df["price"].std()
        sqft_std = df["sqft_living"].std()

        diff_score = np.sqrt(
            ((filtered["price"] - ref_price) / price_std) ** 2
            + ((filtered["sqft_living"] - ref_sqft) / sqft_sqft) ** 2
            if "sqft_sqft" in locals()
            else ((filtered["price"] - ref_price) / price_std) ** 2
            + ((filtered["sqft_living"] - ref_sqft) / sqft_std) ** 2
        )

        similar_indices = diff_score.sort_values().head(max_results).index
        similar_houses = filtered.loc[similar_indices]

        results = []
        for _, row in similar_houses.iterrows():
            results.append(
                {
                    "address": row["street"],
                    "city": row["city"],
                    "price_formatted": f"${row['price']:,.0f} USD",
                    "bedrooms": int(row["bedrooms"]),
                    "bathrooms": float(row["bathrooms"]),
                    "sqft_living": int(row["sqft_living"]),
                    "yr_built": int(row["yr_built"]),
                    "condition": int(row["condition"]),
                }
            )

        return {
            "status": "success",
            "count": len(results),
            "search_criteria": {
                "city": city or "Toàn vùng",
                "target_price": f"${ref_price:,.0f} USD" if target_price else "Mặc định trung vị",
                "sqft_living": f"{ref_sqft:,.0f} sqft" if sqft_living else "Mặc định trung vị",
            },
            "matches": results,
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi tìm kiếm: {str(e)}"}


def explain_price_factors() -> dict:
    """
    Giải thích các yếu tố tác động mạnh nhất đến giá trị nhà ở (Feature Importance từ Random Forest).
    """
    try:
        _, _, _, _, _, feat_imp = get_trained_models()

        top_10 = feat_imp.head(10).round(4).to_dict()
        insights = [
            "1. Diện tích sàn sinh hoạt (sqft_living) chi phối hơn 54% biến thiên giá nhà.",
            "2. Vị trí địa lý đắc địa (các thành phố như Seattle, Bellevue, Medina, Mercer Island) tạo ra chênh lệch đơn giá lớn nhất.",
            "3. Quy mô đất khuôn viên (sqft_lot) và năm xây dựng (yr_built) đóng góp quan trọng tiếp theo.",
            "4. Các yếu tố tầm nhìn đắt giá (view, waterfront) đẩy giá nhà lên nhóm cực đoan cao cấp.",
        ]

        return {
            "status": "success",
            "top_factors_importance_share": top_10,
            "key_market_takeaways": insights,
            "methodology": "Phân tích trích xuất từ mô hình Random Forest Regressor (100 cây quyết định, n_jobs=-1) trên dữ liệu sạch 4,548 căn.",
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
