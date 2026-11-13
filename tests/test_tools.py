"""
Test Suite: tests/test_tools.py
Kiểm thử tự động cho các công cụ trong tools.py — Dữ liệu nhà ở Việt Nam.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import (
    predict_house_price,
    get_market_statistics,
    segment_house,
    explain_market_segments,
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
        self.assertIn("price_range_formatted", res)
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

    def test_tc03_segment_house_thresholds(self):
        """TC03: Phân khúc theo ngưỡng giá cho nhà bình dân và hạng sang."""
        # Nhà bình dân (< 2 tỷ VNĐ)
        res_bd = segment_house(price_billion_vnd=1.2, land_area_m2=60)
        self.assertEqual(res_bd["status"], "success")
        self.assertEqual(res_bd["segment_name"], "Bình dân")
        self.assertIn("tỷ VNĐ", res_bd["price_analyzed"])

        # Nhà hạng sang (> 15 tỷ VNĐ)
        res_hs = segment_house(price_billion_vnd=25.0, land_area_m2=300)
        self.assertEqual(res_hs["status"], "success")
        self.assertEqual(res_hs["segment_name"], "Hạng sang")
        print("✓ TC03 Passed: Budget =", res_bd["segment_name"], "| Luxury =", res_hs["segment_name"])

    def test_tc04_find_similar_houses_vietnam(self):
        """TC04: Tìm kiếm căn nhà tương đồng bằng KNN trên dữ liệu thực tế."""
        res = find_similar_houses(price_billion=3.5, land_area=80, province="Hà Nội", bedrooms=3, limit=3)
        self.assertEqual(res["status"], "success")
        self.assertIn("recommendations", res)
        self.assertGreaterEqual(len(res["recommendations"]), 1)
        rec = res["recommendations"][0]
        self.assertIn("Mã nhà", rec)
        self.assertIn("Loại nhà", rec)
        self.assertIn("Giá bán (Tỷ)", rec)
        self.assertIn("Địa chỉ", rec)
        self.assertIn("Độ sai lệch", rec)
        print("✓ TC04 Passed: Found", len(res["recommendations"]), "houses | Top:", rec["Loại nhà"], rec["Địa chỉ"][:40])

    def test_tc05_explain_price_factors_vietnam(self):
        """TC05: Trích xuất và giải thích Feature Importance từ Random Forest."""
        res = explain_price_factors()
        self.assertEqual(res["status"], "success")
        self.assertIn("top_factors_importance_share", res)
        self.assertGreater(len(res["top_factors_importance_share"]), 0)
        vn_features = {"Diện tích đất", "Diện tích sàn", "Cách trung tâm", "Số tầng", "Phòng ngủ", "Mặt tiền", "Tỉnh/Thành"}
        top_keys = set(res["top_factors_importance_share"].keys())
        overlap = vn_features.intersection(top_keys)
        self.assertGreater(len(overlap), 0, f"Không tìm thấy VN feature trong top factors: {top_keys}")
        print("✓ TC05 Passed: Top feature =", list(res["top_factors_importance_share"].keys())[0])

    def test_tc06_invalid_province_fallback(self):
        """TC06: Xử lý ngoại lệ tỉnh/thành không tồn tại."""
        res = get_market_statistics("TinhKhongTonTai999")
        self.assertEqual(res["status"], "not_found")
        self.assertIn("available_provinces", res)
        print("✓ TC06 Passed: Graceful not_found response handled")

    def test_tc07_explain_market_segments(self):
        """TC07: Mô tả 4 phân khúc thị trường bằng số liệu thật."""
        res = explain_market_segments()
        self.assertEqual(res["status"], "success")
        self.assertIn("segments", res)
        self.assertEqual(len(res["segments"]), 4)
        print("✓ TC07 Passed: 4 segments detailed with actual data")


if __name__ == "__main__":
    unittest.main()
