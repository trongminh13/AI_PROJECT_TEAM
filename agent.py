"""
Module: agent.py
Triển khai AI Agent Orchestrator kết nối OpenRouter API với Tool Calling và Memory:
- Cấu hình OpenAI-compatible client trỏ tới OpenRouter
- Định nghĩa Tool Schema chuẩn OpenAI function calling cho thị trường bất động sản Việt Nam
- Vòng lặp Tool Execution Loop (Model proposes -> Python executes -> Model answers)
- Hỗ trợ fallback cục bộ thông minh nếu không có API key
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from tools import TOOL_CATALOG

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"

SYSTEM_PROMPT = """Bạn là HouseAssist, trợ lý AI chuyên nghiệp phân tích và định giá bất động sản tại thị trường Việt Nam.
Phạm vi chuyên môn: nhà ở tại các tỉnh/thành lớn như Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Bình Dương, Đồng Nai, Cần Thơ và toàn quốc.

Nhiệm vụ và Quy tắc ứng xử:
1. Thân thiện, ngắn gọn, súc tích và có tính học thuật chuyên sâu.
2. Sử dụng các công cụ (Tools) được cung cấp khi người dùng yêu cầu:
   - Dự đoán giá nhà (Tỷ VNĐ) -> Dùng 'predict_house_price'
   - Thống kê thị trường (trung vị, min, max, số lượng giao dịch) -> Dùng 'get_market_statistics'
   - Phân khúc căn nhà (Bình dân, Trung cấp, Cao cấp, Hạng sang) -> Dùng 'segment_house'
   - Tìm kiếm căn nhà tương đồng trong bộ dữ liệu -> Dùng 'find_similar_houses'
   - Giải thích các yếu tố tác động đến giá trị (Feature Importance) -> Dùng 'explain_price_factors'
3. Tuyệt đối không tự bịa đặt số liệu thống kê hoặc giá nhà khi chưa chạy công cụ.
4. Tận dụng ngữ cảnh hội thoại trước đó (Follow-up questions) để điền các tham số còn thiếu.
5. Trả lời bằng tiếng Việt chuyên nghiệp, định dạng số tiền rõ ràng (Tỷ VNĐ / triệu/m²), kèm nhận xét thực tế.

Đơn vị chuẩn:
- Giá: Tỷ VNĐ (tỷ đồng). Ví dụ: 3.5 tỷ VNĐ.
- Đơn giá: Triệu VNĐ/m². Ví dụ: 45 triệu/m².
- Diện tích: m² (mét vuông). Ví dụ: 80 m².
- Khoảng cách: km. Ví dụ: 5 km từ trung tâm.

Phân khúc thị trường Việt Nam:
- Bình dân: < 2 tỷ VNĐ
- Trung cấp: 2–5 tỷ VNĐ
- Cao cấp: 5–15 tỷ VNĐ
- Hạng sang: > 15 tỷ VNĐ
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "predict_house_price",
            "description": "Dự đoán giá bán căn nhà (Tỷ VNĐ) tại thị trường Việt Nam bằng mô hình Machine Learning Random Forest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "land_area": {
                        "type": "number",
                        "description": "Diện tích đất (m², ví dụ 60, 80, 120)",
                    },
                    "province": {
                        "type": "string",
                        "description": "Tỉnh/Thành phố (ví dụ Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Bình Dương...)",
                    },
                    "floor_area": {
                        "type": "number",
                        "description": "Tổng diện tích sàn (m², nếu không cung cấp sẽ tính từ land_area * floors)",
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Số phòng ngủ (mặc định 3)",
                    },
                    "bathrooms": {
                        "type": "number",
                        "description": "Số phòng tắm (ví dụ 1.0, 2.0, 3.0)",
                    },
                    "floors": {
                        "type": "number",
                        "description": "Số tầng (ví dụ 1, 2, 3, 4)",
                    },
                    "distance_to_center": {
                        "type": "number",
                        "description": "Khoảng cách đến trung tâm thành phố (km, ví dụ 3.0, 5.0, 10.0)",
                    },
                    "property_type": {
                        "type": "string",
                        "description": "Loại bất động sản (ví dụ: Nhà phố, Nhà cấp 4, Biệt thự, Chung cư)",
                    },
                    "house_age": {
                        "type": "number",
                        "description": "Tuổi nhà (năm, ví dụ 0 = mới xây, 10, 20)",
                    },
                },
                "required": ["land_area"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_statistics",
            "description": "Lấy số liệu thống kê thị trường bất động sản (giá trung vị, trung bình, min, max, đơn giá/m²) toàn quốc hoặc theo từng tỉnh/thành cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "Tên tỉnh/thành phố cần tra cứu (ví dụ Hà Nội, Đà Nẵng, Bình Dương) hoặc để trống nếu muốn xem toàn quốc.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "segment_house",
            "description": "Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp / Hạng sang) dựa trên giá bán và diện tích đất sử dụng thuật toán K-Means.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price_billion_vnd": {
                        "type": "number",
                        "description": "Giá bán của căn nhà (Tỷ VNĐ, ví dụ 1.5, 3.5, 10.0)",
                    },
                    "land_area_m2": {
                        "type": "number",
                        "description": "Diện tích đất (m², ví dụ 60, 80, 150)",
                    },
                },
                "required": ["price_billion_vnd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_houses",
            "description": "Tìm kiếm các căn nhà thực tế tương tự trong bộ dữ liệu Việt Nam theo tỉnh/thành, ngân sách giá hoặc diện tích.",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "Tỉnh/Thành phố mong muốn tìm (ví dụ Hà Nội, TP. Hồ Chí Minh)",
                    },
                    "target_price_billion": {
                        "type": "number",
                        "description": "Ngân sách giá mong muốn (Tỷ VNĐ, ví dụ 2.5, 5.0)",
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Số phòng ngủ mong muốn",
                    },
                    "land_area_m2": {
                        "type": "number",
                        "description": "Diện tích đất mong muốn (m²)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Số lượng căn muốn xem (mặc định 3)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_price_factors",
            "description": "Trích xuất các yếu tố chi phối giá nhà tại Việt Nam từ mô hình Random Forest (Feature Importance) và giải thích logic định giá.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def execute_tool_call(tool_name: str, arguments: dict) -> dict:
    """Thực thi một tool call được đề xuất từ LLM."""
    if tool_name not in TOOL_CATALOG:
        return {"status": "error", "message": f"Công cụ '{tool_name}' không tồn tại."}

    func = TOOL_CATALOG[tool_name]
    try:
        result = func(**arguments)
        return result
    except Exception as e:
        return {"status": "error", "message": f"Lỗi thực thi tool '{tool_name}': {str(e)}"}


def run_agent_turn(
    messages: list,
    api_key: str = None,
    model: str = DEFAULT_MODEL,
    site_url: str = "http://localhost:8501",
    site_name: str = "HouseAssist",
) -> tuple[str, list]:
    """
    Thực thi 1 lượt phản hồi của Agent với đầy đủ chu trình Tool Calling và Stateful Memory.
    Trả về: (câu trả lời cuối cùng, danh sách các tool calls đã diễn ra).
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY", "")

    # Chuẩn bị hội thoại bao gồm System Prompt nếu chưa có
    full_messages = []
    if not messages or messages[0].get("role") != "system":
        full_messages.append({"role": "system", "content": SYSTEM_PROMPT})
    full_messages.extend(messages)

    tool_logs = []

    # Nếu không có API Key, sử dụng bộ điều phối Heuristic Fallback
    if not api_key:
        fallback_ans, fallback_tools = _run_heuristic_fallback(messages[-1]["content"])
        return fallback_ans, fallback_tools

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": site_url,
            "X-Title": site_name,
        },
    )

    try:
        # Lượt 1: Gửi hội thoại và danh sách tool schema đến LLM
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )

        response_message = response.choices[0].message

        # Kiểm tra nếu LLM quyết định gọi công cụ
        if response_message.tool_calls:
            # Lưu lại yêu cầu gọi tool vào hội thoại
            full_messages.append(response_message)

            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except Exception:
                    fn_args = {}

                tool_result = execute_tool_call(fn_name, fn_args)
                tool_logs.append({
                    "tool_name": fn_name,
                    "arguments": fn_args,
                    "result": tool_result,
                })

                # Đưa kết quả thực thi tool trở lại hội thoại
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

            # Lượt 2: LLM tổng hợp kết quả công cụ thành câu trả lời tự nhiên
            second_response = client.chat.completions.create(
                model=model,
                messages=full_messages,
                temperature=0.3,
            )
            final_content = second_response.choices[0].message.content
            return final_content, tool_logs
        else:
            # LLM trả lời trực tiếp không cần tool
            return response_message.content or "Tôi có thể hỗ trợ gì thêm về thị trường bất động sản Việt Nam?", tool_logs

    except Exception as e:
        error_msg = str(e)
        # Nếu gặp lỗi OpenRouter, chuyển sang fallback để đảm bảo ứng dụng không dừng
        fallback_ans, fallback_tools = _run_heuristic_fallback(messages[-1]["content"])
        warning_note = f"\n\n*(Lưu ý: Đã kích hoạt chế độ phân tích ngoại tuyến do kết nối OpenRouter gặp lỗi: {error_msg[:100]})*"
        return fallback_ans + warning_note, fallback_tools


def _run_heuristic_fallback(user_text: str) -> tuple[str, list]:
    """Bộ điều phối thông minh chạy cục bộ khi không có mạng hoặc chưa nhập OpenRouter key."""
    import re
    text_lower = user_text.lower()
    tool_logs = []

    # 0. Kiểm tra địa danh quốc tế / ngoài phạm vi hỗ trợ
    foreign_cities = ["tokyo", "paris", "london", "new york", "seattle", "bắc kinh", "bangkok", "singapore", "sao hỏa", "berlin", "sydney"]
    if any(c in text_lower for c in foreign_cities):
        res = TOOL_CATALOG["get_market_statistics"]("QuocTe")
        tool_logs.append({"tool_name": "get_market_statistics", "arguments": {"province": "QuocTe"}, "result": res})
        ans = "### Thông Báo Phạm Vi Dữ Liệu:\n"
        ans += "Hiện tại hệ thống **HouseAssist** chỉ hỗ trợ phân tích và định giá bất động sản tại thị trường **Việt Nam** (như Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Bình Dương, Đồng Nai, Cần Thơ...).\n\n"
        ans += "Hệ thống chưa hỗ trợ dữ liệu tại các thành phố quốc tế. Bạn vui lòng tra cứu theo các tỉnh/thành tại Việt Nam nhé!"
        return ans, tool_logs

    def _extract_province(t: str):
        province_map = {
            "hà nội": "Hà Nội",
            "hồ chí minh": "TP. Hồ Chí Minh",
            "tp.hcm": "TP. Hồ Chí Minh",
            "tphcm": "TP. Hồ Chí Minh",
            "sài gòn": "TP. Hồ Chí Minh",
            "đà nẵng": "Đà Nẵng",
            "bình dương": "Bình Dương",
            "đồng nai": "Đồng Nai",
            "cần thơ": "Cần Thơ",
            "hải phòng": "Hải Phòng",
            "nha trang": "Khánh Hòa",
            "khánh hòa": "Khánh Hòa",
            "vũng tàu": "Bà Rịa - Vũng Tàu",
            "huế": "Huế",
        }
        for p, name in province_map.items():
            if p in t:
                return name
        return None

    # Trích xuất các tham số số học cơ bản
    detected_prov = _extract_province(text_lower)
    m_price = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:tỷ|ty|billion)", text_lower)
    m_area = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²|mét vuông)", text_lower)
    m_bed = re.search(r"(\d+)\s*(?:phòng ngủ|pn|phòng)", text_lower)
    m_bath = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:phòng tắm|pt|wc|toilet)", text_lower)
    m_floor = re.search(r"(\d+)\s*(?:tầng)", text_lower)

    # 1. Phân khúc nhà (Ưu tiên kiểm tra trước Thống kê thị trường để tránh xung đột từ "thị trường")
    if any(k in text_lower for k in ["phân khúc", "segment", "hạng sang", "bình dân", "trung cấp", "cao cấp"]):
        price = float(m_price.group(1).replace(",", ".")) if m_price else 3.5
        area = float(m_area.group(1).replace(",", ".")) if m_area else 80.0
        res = TOOL_CATALOG["segment_house"](price_billion_vnd=price, land_area_m2=area)
        tool_logs.append({"tool_name": "segment_house", "arguments": {"price_billion_vnd": price, "land_area_m2": area}, "result": res})
        ans = f"### Phân Khúc Bất Động Sản Việt Nam (K-Means Clustering):\n"
        ans += f"- **Phân khúc:** {res['segment_name']}\n"
        ans += f"- **Mức giá phân tích:** {res['price_analyzed']}\n"
        ans += f"- **Diện tích phân tích:** {res['area_analyzed']}\n"
        ans += f"- **Đặc điểm thị trường:** {res['market_profile']}\n"
        return ans, tool_logs

    # 2. Tìm kiếm căn nhà thực tế tương đồng
    if any(k in text_lower for k in ["tìm", "căn nhà thực tế", "tương đồng", "tương tự", "nhà mẫu", "gợi ý căn", "find"]):
        prov = detected_prov or "Hà Nội"
        target_price = float(m_price.group(1).replace(",", ".")) if m_price else None
        bedrooms = int(m_bed.group(1)) if m_bed else 3
        kwargs = {"province": prov, "bedrooms": bedrooms, "max_results": 3}
        if target_price:
            kwargs["target_price_billion"] = target_price
        res = TOOL_CATALOG["find_similar_houses"](**kwargs)
        tool_logs.append({"tool_name": "find_similar_houses", "arguments": kwargs, "result": res})
        ans = f"### Các Căn Nhà Thực Tế Tương Đồng Tại {prov} (Bộ Dữ Liệu house_cleaned.csv):\n"
        for idx, h in enumerate(res.get("matches", []), 1):
            name = h.get("display_name") or f"Nhà tại {h.get('province', 'Việt Nam')}"
            ans += f"{idx}. **{name} — {h.get('province')}, {h.get('district', '')}**\n"
            if h.get("full_address"):
                ans += f"   - Địa chỉ: `{h['full_address']}`\n"
            ans += f"   - Giá: `{h['price_formatted']}` | Đơn giá: `{h['price_per_m2']}` ({h.get('price_segment', '')})\n"
            ans += f"   - Diện tích đất: `{h['land_area_m2']} m²` | {h['bedrooms']} PN, {h['bathrooms']} PT, {h.get('floors', 1)} tầng\n"
            legal = h.get("legal_status") or "Đang cập nhật"
            furn = h.get("furniture_state") or "Không rõ"
            ans += f"   - Pháp lý: {legal} | Nội thất: {furn}\n"
        return ans, tool_logs

    # 3. Yếu tố chi phối giá (Feature Importance)
    if any(k in text_lower for k in ["yếu tố", "quan trọng", "ảnh hưởng", "feature importance", "tại sao giá", "tác động"]):
        res = TOOL_CATALOG["explain_price_factors"]()
        tool_logs.append({"tool_name": "explain_price_factors", "arguments": {}, "result": res})
        ans = "### Các Yếu Tố Chi Phối Giá Nhà tại Việt Nam (Mô hình Random Forest):\n"
        for insight in res.get("key_market_takeaways", []):
            ans += f"- {insight}\n"
        ans += "\n**Tỷ lệ quan trọng của Top 5 đặc trưng:**\n"
        for k, v in list(res.get("top_factors_importance_share", {}).items())[:5]:
            ans += f"- `{k}`: {v*100:.1f}%\n"
        return ans, tool_logs

    # 4. Thống kê thị trường
    if any(k in text_lower for k in ["thống kê", "thị trường", "trung bình", "median", "bao nhiêu căn", "tổng số", "market"]):
        res = TOOL_CATALOG["get_market_statistics"](province=detected_prov)
        tool_logs.append({"tool_name": "get_market_statistics", "arguments": {"province": detected_prov}, "result": res})
        ans = f"### Báo cáo Thống kê Thị trường ({res.get('scope', 'Việt Nam')}):\n"
        ans += f"- **Tổng số giao dịch ghi nhận:** {res.get('total_listings', 0):,} căn\n"
        ans += f"- **Giá trung vị (Median):** {res.get('median_price_formatted', 'N/A')}\n"
        ans += f"- **Giá trung bình:** {res.get('mean_price_formatted', 'N/A')}\n"
        ans += f"- **Đơn giá trung bình:** {res.get('avg_price_per_m2', 'N/A')}\n"
        if "top_5_expensive_provinces" in res:
            ans += "\n**Top 5 tỉnh/thành có giá trung vị cao nhất:**\n"
            for k, v in res["top_5_expensive_provinces"].items():
                ans += f"- {k}: {v}\n"
        return ans, tool_logs

    # 5. Mặc định: Dự đoán giá nhà (Random Forest)
    land_area = float(m_area.group(1).replace(",", ".")) if m_area else 80.0
    province = detected_prov or "Hà Nội"
    bedrooms = int(m_bed.group(1)) if m_bed else 3
    bathrooms = float(m_bath.group(1).replace(",", ".")) if m_bath else 2.0
    floors = int(m_floor.group(1)) if m_floor else 3

    kwargs = {
        "land_area": land_area,
        "province": province,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "floors": floors,
    }
    res = TOOL_CATALOG["predict_house_price"](**kwargs)
    tool_logs.append({"tool_name": "predict_house_price", "arguments": kwargs, "result": res})
    ans = f"### Ước Tính Định Giá Bất Động Sản Việt Nam (Mô hình Random Forest):\n"
    ans += f"- **Tỉnh/Thành:** {province}\n"
    ans += f"- **Thông số nhà:** {land_area:.0f} m², {bedrooms} PN, {bathrooms:.0f} PT, {floors} tầng\n"
    ans += f"- **Giá dự đoán điểm:** {res['estimated_price_formatted']}\n"
    ans += f"- **Khoảng dao động tin cậy (88–112%):** {res['price_range_formatted']}\n"
    ans += f"- **Đơn giá ước tính:** {res['price_per_m2_formatted']}\n"
    ans += "\n*(Bạn có thể cung cấp thêm diện tích, số tầng hoặc quận/huyện để định giá chi tiết hơn!)*"
    return ans, tool_logs
