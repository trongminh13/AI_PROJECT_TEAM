"""
Test Suite: tests/test_tools.py
Kiểm thử tự động cho 5 công cụ trong tools.py — Dữ liệu nhà ở Việt Nam.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import (
    predict_house_price,
    get_market_statistics,
    segment_house,
    find_similar_houses,
    explain_price_factors,
)


class TestRealEstateToolsVietnam(unittest.TestCase):
    def test_tc01_predict_house_price_hanoi(self):
        """TC01: Dự đoán giá nhà phố 80m² tại Hà Nội."""
        res = predict_house_price(land_area=80, province="Hà Nội", bedrooms=3, bathrooms=2.0, floors=3)
        self.assertEqual(res["status"], "success")
        self.assertIn("estimated_price_billion_vnd", res)
        self.assertGreater(res["estimated_price_billion_vnd"], 0)
        self.assertIn("tỷ VNĐ", res["estimated_price_formatted"])
        print("✓ TC01 Passed:", res["estimated_price_formatted"])

    def test_tc02_market_statistics_overall_and_province(self):
        """TC02: Thống kê toàn quốc và theo tỉnh/thành."""
        # Toàn quốc
        res_all = get_market_statistics()
        self.assertEqual(res_all["status"], "success")
        self.assertGreater(res_all["total_listings"], 1000)
        self.assertIn("median_price_formatted", res_all)

        # Theo tỉnh (dùng tỉnh có trong dataset)
        res_prov = get_market_statistics("Đà Nẵng")
        self.assertEqual(res_prov["status"], "success")
        self.assertGreater(res_prov["total_listings"], 0)
        print("✓ TC02 Passed: Total =", res_all["total_listings"], "| Đà Nẵng =", res_prov["total_listings"])

    def test_tc03_segment_house_kmeans(self):
        """TC03: Phân khúc K-Means cho nhà bình dân và hạng sang."""
        # Nhà bình dân (~1 tỷ VNĐ)
        res_bd = segment_house(price_billion_vnd=1.2, land_area_m2=60)
        self.assertEqual(res_bd["status"], "success")
        self.assertEqual(res_bd["segment_id"], 0)  # Bình dân
        self.assertIn("tỷ VNĐ", res_bd["price_analyzed"])

        # Nhà hạng sang (>20 tỷ VNĐ)
        res_hs = segment_house(price_billion_vnd=25.0, land_area_m2=300)
        self.assertEqual(res_hs["status"], "success")
        self.assertEqual(res_hs["segment_id"], 3)  # Hạng sang
        print("✓ TC03 Passed: Budget =", res_bd["segment_name"], "| Luxury =", res_hs["segment_name"])

    def test_tc04_find_similar_houses_vietnam(self):
        """TC04: Tìm kiếm căn nhà tương đồng — dùng house_cleaned.csv (địa chỉ & dự án thực tế)."""
        res = find_similar_houses(province="Hà Nội", target_price_billion=3.5, bedrooms=3, max_results=3)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["matches"]), 1)
        # Kiểm tra các field mới từ house_cleaned.csv
        match = res["matches"][0]
        self.assertIn("full_address", match)
        self.assertIn("display_name", match)
        self.assertIn("province", match)
        self.assertIn("price_formatted", match)
        self.assertIn("price_segment", match)
        # Kiểm tra nguồn dữ liệu đúng
        self.assertIn("data_source", res)
        self.assertIn("house_cleaned.csv", res["data_source"])
        print("✓ TC04 Passed: Found", len(res["matches"]), "| display_name =", match["display_name"][:40])


    def test_tc05_explain_price_factors_vietnam(self):
        """TC05: Trích xuất và giải thích Feature Importance từ Random Forest (VN data)."""
        res = explain_price_factors()
        self.assertEqual(res["status"], "success")
        self.assertIn("top_factors_importance_share", res)
        self.assertGreater(len(res["top_factors_importance_share"]), 0)
        # Kiểm tra có ít nhất 1 feature VN-specific trong top factors
        vn_features = {"Land_Area", "Floor_Area", "Distance_To_Center", "Floors", "Bedrooms", "Frontage"}
        top_keys = set(res["top_factors_importance_share"].keys())
        overlap = vn_features.intersection(top_keys)
        self.assertGreater(len(overlap), 0, f"Không tìm thấy VN feature trong top factors: {top_keys}")
        print("✓ TC05 Passed: Top feature =", list(res["top_factors_importance_share"].keys())[0])

    def test_tc06_invalid_province_fallback(self):
        """TC06: Xử lý ngoại lệ tỉnh/thành không tồn tại."""
        res = get_market_statistics("TinhKhongTonTai999")
        self.assertEqual(res["status"], "not_found")
        self.assertIn("available_provinces_sample", res)
        print("✓ TC06 Passed: Graceful not_found response handled")


if __name__ == "__main__":
    unittest.main()
