"""
Module: agent.py
Triển khai AI Agent Orchestrator kết nối OpenRouter API với Tool Calling và Memory:
- Cấu hình OpenAI-compatible client trỏ tới OpenRouter
- Định nghĩa Tool Schema chuẩn OpenAI function calling
- Vòng lặp Tool Execution Loop (Model proposes -> Python executes -> Model answers)
- Hỗ trợ fallback cục bộ thông minh nếu không có API key
"""

import os
import json
from openai import OpenAI
from tools import TOOL_CATALOG

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"

SYSTEM_PROMPT = """Bạn là HouseAssist, trợ lý AI chuyên nghiệp phân tích và định giá bất động sản tại vùng King County, bang Washington (khu vực Seattle, Bellevue, Redmond, Kirkland, Kent...).

Nhiệm vụ và Quy tắc ứng xử:
1. Thân thiện, ngắn gọn, súc tích và có tính học thuật chuyên sâu.
2. Sử dụng các công cụ (Tools) được cung cấp khi người dùng yêu cầu:
   - Dự đoán giá nhà -> Dùng 'predict_house_price'
   - Thống kê thị trường (trung vị, min, max, số lượng giao dịch) -> Dùng 'get_market_statistics'
   - Phân khúc căn nhà (Bình dân, Trung cấp, Cao cấp) -> Dùng 'segment_house'
   - Tìm kiếm căn nhà tương đồng trong bộ dữ liệu -> Dùng 'find_similar_houses'
   - Giải thích các yếu tố tác động đến giá trị (Feature Importance) -> Dùng 'explain_price_factors'
3. Tuyệt đối không tự bịa đặt số liệu thống kê hoặc giá nhà khi chưa chạy công cụ.
4. Tận dụng ngữ cảnh hội thoại trước đó (Follow-up questions) để điền các tham số còn thiếu (ví dụ nếu người dùng vừa dự đoán giá nhà ở Seattle 2000 sqft, câu sau hỏi "căn này thuộc phân khúc nào?" thì lấy giá và diện tích vừa tính).
5. Trả lời bằng tiếng Việt chuyên nghiệp, định dạng số tiền rõ ràng (USD), kèm theo nhận xét ý nghĩa thực tế.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "predict_house_price",
            "description": "Dự đoán giá bán căn nhà (USD) tại King County bằng mô hình Machine Learning Random Forest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sqft_living": {
                        "type": "number",
                        "description": "Diện tích sàn sinh hoạt (square feet, ví dụ 1500, 2000, 3200)",
                    },
                    "city": {
                        "type": "string",
                        "description": "Thành phố tại King County (ví dụ Seattle, Bellevue, Redmond, Kent, Renton...)",
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Số phòng ngủ (mặc định 3)",
                    },
                    "bathrooms": {
                        "type": "number",
                        "description": "Số phòng tắm (ví dụ 1.5, 2.0, 2.5)",
                    },
                    "sqft_lot": {
                        "type": "number",
                        "description": "Diện tích đất khuôn viên (square feet, ví dụ 5000, 7500)",
                    },
                    "floors": {
                        "type": "number",
                        "description": "Số tầng (ví dụ 1.0, 1.5, 2.0)",
                    },
                    "waterfront": {
                        "type": "integer",
                        "description": "Ven sông/hồ (1 là có, 0 là không)",
                    },
                    "view": {
                        "type": "integer",
                        "description": "Độ đẹp của tầm nhìn từ 0 đến 4",
                    },
                    "condition": {
                        "type": "integer",
                        "description": "Tình trạng nhà từ 1 (kém) đến 5 (rất tốt)",
                    },
                    "yr_built": {
                        "type": "integer",
                        "description": "Năm xây dựng (ví dụ 1980, 2005)",
                    },
                },
                "required": ["sqft_living"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_statistics",
            "description": "Lấy số liệu thống kê thị trường (giá trung vị, trung bình, min, max, đơn giá/sqft) toàn vùng King County hoặc theo từng thành phố cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Tên thành phố cần tra cứu (ví dụ Seattle, Bellevue, Renton, Kirkland) hoặc để trống nếu muốn xem toàn vùng.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "segment_house",
            "description": "Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp) dựa trên giá bán và diện tích sàn sử dụng thuật toán K-Means.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {
                        "type": "number",
                        "description": "Giá bán của căn nhà (USD)",
                    },
                    "sqft_living": {
                        "type": "number",
                        "description": "Diện tích sàn sinh hoạt (square feet)",
                    },
                },
                "required": ["price", "sqft_living"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_houses",
            "description": "Tìm kiếm các căn nhà thực tế tương tự trong bộ dữ liệu King County theo thành phố, ngân sách giá hoặc diện tích.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Thành phố mong muốn tìm",
                    },
                    "target_price": {
                        "type": "number",
                        "description": "Ngân sách giá mong muốn (USD)",
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Số phòng ngủ mong muốn",
                    },
                    "sqft_living": {
                        "type": "number",
                        "description": "Diện tích sàn mong muốn (sqft)",
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
            "description": "Trích xuất các yếu tố chi phối giá nhà từ mô hình Random Forest (Feature Importance) và giải thích logic định giá.",
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
            return response_message.content or "Tôi có thể hỗ trợ gì thêm cho bạn về giá nhà King County?", tool_logs

    except Exception as e:
        error_msg = str(e)
        # Nếu gặp lỗi OpenRouter (như 401, quota, connection), chuyển sang fallback để đảm bảo ứng dụng không dừng
        fallback_ans, fallback_tools = _run_heuristic_fallback(messages[-1]["content"])
        warning_note = f"\n\n*(Lưu ý: Đã kích hoạt chế độ phân tích ngoại tuyến do kết nối OpenRouter gặp lỗi: {error_msg[:100]})*"
        return fallback_ans + warning_note, fallback_tools


def _run_heuristic_fallback(user_text: str) -> tuple[str, list]:
    """Bộ điều phối thông minh chạy cục bộ khi không có mạng hoặc chưa nhập OpenRouter key."""
    text_lower = user_text.lower()
    tool_logs = []

    # 1. Thống kê thị trường
    if any(k in text_lower for k in ["thống kê", "thị trường", "trung bình", "median", "bao nhiêu căn", "tổng số", "market"]):
        city_found = None
        for c in ["seattle", "bellevue", "redmond", "kirkland", "renton", "kent", "federal way"]:
            if c in text_lower:
                city_found = c.title()
                break
        res = TOOL_CATALOG["get_market_statistics"](city=city_found)
        tool_logs.append({"tool_name": "get_market_statistics", "arguments": {"city": city_found}, "result": res})
        ans = f"### Báo cáo Thống kê Thị trường ({res.get('scope', 'King County')}):\n"
        ans += f"- **Tổng số giao dịch ghi nhận:** {res.get('total_transactions', 0):,} căn\n"
        ans += f"- **Giá trung vị (Median):** {res.get('median_price_formatted', 'N/A')}\n"
        ans += f"- **Giá trung bình:** {res.get('mean_price_formatted', 'N/A')}\n"
        ans += f"- **Đơn giá trung bình:** {res.get('avg_price_per_sqft', 'N/A')}\n"
        if "top_5_expensive_cities_by_median" in res:
            ans += "\n**Top 5 thành phố có giá trung vị cao nhất:**\n"
            for k, v in res["top_5_expensive_cities_by_median"].items():
                ans += f"- {k}: {v}\n"
        return ans, tool_logs

    # 2. Yếu tố chi phối giá
    if any(k in text_lower for k in ["yếu tố", "quan trọng", "ảnh hưởng", "feature importance", "tại sao giá", "tác động"]):
        res = TOOL_CATALOG["explain_price_factors"]()
        tool_logs.append({"tool_name": "explain_price_factors", "arguments": {}, "result": res})
        ans = "### Các Yếu Tố Chi Phối Giá Nhà tại King County (Mô hình Random Forest):\n"
        for insight in res.get("key_market_takeaways", []):
            ans += f"- {insight}\n"
        ans += "\n**Tỷ lệ quan trọng của Top 5 đặc trưng:**\n"
        for k, v in list(res.get("top_factors_importance_share", {}).items())[:5]:
            ans += f"- `{k}`: {v*100:.1f}%\n"
        return ans, tool_logs

    # 3. Phân khúc nhà
    if any(k in text_lower for k in ["phân khúc", "bình dân", "trung cấp", "cao cấp", "segment"]):
        # Lấy số nếu có
        import re
        nums = re.findall(r"\d+", text_lower.replace(",", "").replace(".", ""))
        price = 550000.0
        sqft = 2000.0
        if len(nums) >= 2:
            price = float(nums[0]) if float(nums[0]) > 10000 else float(nums[1])
            sqft = float(nums[1]) if float(nums[0]) > 10000 else float(nums[0])
        res = TOOL_CATALOG["segment_house"](price=price, sqft_living=sqft)
        tool_logs.append({"tool_name": "segment_house", "arguments": {"price": price, "sqft_living": sqft}, "result": res})
        ans = f"### Phân Khúc Bất Động Sản (K-Means Clustering):\n"
        ans += f"- **Phân khúc:** {res['segment_name']}\n"
        ans += f"- **Mức giá phân tích:** {res['price_analyzed']}\n"
        ans += f"- **Diện tích phân tích:** {res['sqft_analyzed']}\n"
        ans += f"- **Đặc điểm thị trường:** {res['market_profile']}\n"
        return ans, tool_logs

    # 4. Tìm kiếm nhà tương đồng
    if any(k in text_lower for k in ["tìm nhà", "tìm kiếm", "căn nhà tương tự", "tương đồng", "find"]):
        res = TOOL_CATALOG["find_similar_houses"](city="Seattle", max_results=3)
        tool_logs.append({"tool_name": "find_similar_houses", "arguments": {"city": "Seattle"}, "result": res})
        ans = "### Các Căn Nhà Tương Đồng Tiêu Biểu Trong Bộ Dữ Liệu:\n"
        for idx, h in enumerate(res.get("matches", []), 1):
            ans += f"{idx}. **{h['address']}, {h['city']}**\n"
            ans += f"   - Giá: `{h['price_formatted']}` | Diện tích: `{h['sqft_living']} sqft`\n"
            ans += f"   - Cấu trúc: {h['bedrooms']} phòng ngủ, {h['bathrooms']} phòng tắm, xây năm {h['yr_built']}\n"
        return ans, tool_logs

    # 5. Mặc định: Dự đoán giá nhà
    res = TOOL_CATALOG["predict_house_price"](sqft_living=2000, city="Seattle", bedrooms=3, bathrooms=2.0)
    tool_logs.append({"tool_name": "predict_house_price", "arguments": {"sqft_living": 2000, "city": "Seattle"}, "result": res})
    ans = f"### Ước Tính Định Giá Bất Động Sản (Mô hình Random Forest):\n"
    ans += f"- **Giá dự đoán điểm:** {res['estimated_price_formatted']}\n"
    ans += f"- **Khoảng dao động tin cậy (90%):** {res['price_range_formatted']}\n"
    ans += f"- **Đơn giá ước tính:** ${res['price_per_sqft_usd']}/sqft\n"
    ans += f"- **Thông số mặc định sử dụng:** Nhà 2,000 sqft, 3 phòng ngủ, 2 phòng tắm tại Seattle.\n"
    ans += "\n*(Bạn có thể cung cấp chi tiết diện tích, số phòng và thành phố để tôi định giá chính xác hơn!)*"
    return ans, tool_logs
