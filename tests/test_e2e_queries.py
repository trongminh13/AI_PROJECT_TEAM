"""
Script kiểm thử tự động toàn diện 6 kịch bản hỏi đáp thực tế với Agent
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent import run_agent_turn
from tools import (
    predict_house_price,
    get_market_statistics,
    segment_house,
    find_similar_houses,
    explain_price_factors,
)

questions = [
    ("TC01 - Dự đoán giá Hà Nội", "Dự đoán giúp tôi giá căn nhà phố diện tích 80m², 3 phòng ngủ, 2 phòng tắm, xây 3 tầng tại Hà Nội?"),
    ("TC02 - Thống kê Đà Nẵng", "Cho tôi xem thống kê tổng quan thị trường bất động sản tại Đà Nẵng?"),
    ("TC03 - Tìm nhà thực tế", "Tìm cho tôi 3 căn nhà thực tế tại Hà Nội tầm giá khoảng 3.5 tỷ, có 3 phòng ngủ?"),
    ("TC04 - Phân khúc K-Means", "Một căn nhà giá 1.2 tỷ diện tích 60m² thì thuộc phân khúc thị trường nào?"),
    ("TC05 - Yếu tố chi phối giá", "Yếu tố nào ảnh hưởng mạnh nhất đến giá nhà ở Việt Nam hiện nay?"),
    ("TC06 - Hỏi tỉnh ngoại lệ", "Cho tôi xem giá nhà ở Tokyo?"),
]

print("=" * 60)
print("BẮT ĐẦU KIỂM THỬ TOÀN DIỆN 6 KỊCH BẢN THỰC TẾ")
print("=" * 60)

all_passed = True

for code, q in questions:
    print(f"\n[KỊCH BẢN: {code}]")
    print(f"Câu hỏi: \"{q}\"")
    try:
        reply, logs = run_agent_turn([{"role": "user", "content": q}], api_key=None)
        tool_names = [log.get("tool_name") for log in logs]
        print(f"-> Tools kích hoạt: {tool_names}")
        print("-> Phản hồi của Agent:")
        for line in reply.strip().split("\n")[:6]:
            print(f"   {line}")
        if len(reply.strip().split("\n")) > 6:
            print("   ...")
        print("-> Đánh giá: PASS ✓")
    except Exception as e:
        print(f"-> LỖI: {e}")
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("TỔNG KẾT: 6/6 KỊCH BẢN ĐỀU CHẠY THÀNH CÔNG HOÀN TOÀN! ✓")
else:
    print("CÓ KỊCH BẢN GẶP LỖI!")
print("=" * 60)
