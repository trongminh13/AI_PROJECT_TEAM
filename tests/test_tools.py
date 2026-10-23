"""
Test Suite: tests/test_tools.py
Kiểm thử tự động cho 5 công cụ trong tools.py theo tiêu chuẩn Task 7 của Jetking Lesson.
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


class TestRealEstateTools(unittest.TestCase):
    def test_tc01_predict_house_price(self):
        """TC01: Dự đoán giá nhà với thông số tiêu chuẩn ở Seattle."""
        res = predict_house_price(sqft_living=2000, city="Seattle", bedrooms=3, bathrooms=2.0)
        self.assertEqual(res["status"], "success")
        self.assertIn("estimated_price_usd", res)
        self.assertGreater(res["estimated_price_usd"], 100000)
        print("✓ TC01 Passed:", res["estimated_price_formatted"])

    def test_tc02_market_statistics_overall_and_city(self):
        """TC02: Thống kê toàn vùng King County và theo thành phố Seattle."""
        # Toàn vùng
        res_all = get_market_statistics()
        self.assertEqual(res_all["status"], "success")
        self.assertEqual(res_all["total_transactions"], 4548)
        self.assertIn("median_price_formatted", res_all)

        # Theo thành phố
        res_sea = get_market_statistics("Seattle")
        self.assertEqual(res_sea["status"], "success")
        self.assertGreater(res_sea["total_transactions"], 1000)
        print("✓ TC02 Passed: Overall count =", res_all["total_transactions"], ", Seattle =", res_sea["total_transactions"])

    def test_tc03_segment_house_kmeans(self):
        """TC03: Phân khúc K-Means cho nhà giá rẻ và biệt thự triệu đô."""
        res_budget = segment_house(price=280000, sqft_living=1200)
        self.assertEqual(res_budget["status"], "success")
        self.assertEqual(res_budget["segment_id"], 0)  # Bình dân

        res_luxury = segment_house(price=1500000, sqft_living=4000)
        self.assertEqual(res_luxury["status"], "success")
        self.assertEqual(res_luxury["segment_id"], 2)  # Cao cấp
        print("✓ TC03 Passed: Budget =", res_budget["segment_name"], "| Luxury =", res_luxury["segment_name"])

    def test_tc04_find_similar_houses(self):
        """TC04: Tìm kiếm các căn nhà tương đồng trong bộ dữ liệu."""
        res = find_similar_houses(city="Bellevue", target_price=600000, bedrooms=3, max_results=3)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["matches"]), 1)
        self.assertIn("address", res["matches"][0])
        print("✓ TC04 Passed: Found", len(res["matches"]), "similar houses in Bellevue")

    def test_tc05_explain_price_factors(self):
        """TC05: Trích xuất và giải thích Feature Importance từ Random Forest."""
        res = explain_price_factors()
        self.assertEqual(res["status"], "success")
        self.assertIn("sqft_living", res["top_factors_importance_share"])
        self.assertGreater(res["top_factors_importance_share"]["sqft_living"], 0.40)
        print("✓ TC05 Passed: sqft_living share =", res["top_factors_importance_share"]["sqft_living"])

    def test_tc06_invalid_city_fallback(self):
        """TC06: Xử lý ngoại lệ thành phố không tồn tại."""
        res = get_market_statistics("CityNotExist999")
        self.assertEqual(res["status"], "not_found")
        print("✓ TC06 Passed: Graceful not_found response handled")


if __name__ == "__main__":
    unittest.main()
