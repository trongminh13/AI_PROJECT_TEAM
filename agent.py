"""
Module: agent.py
Triển khai AI Agent Orchestrator kết nối OpenRouter API với Tool Calling và Memory:
- Cấu hình OpenAI-compatible client trỏ tới OpenRouter
- Định nghĩa Tool Schema chuẩn OpenAI function calling cho thị trường bất động sản Việt Nam
- Vòng lặp Tool Execution Loop (Model proposes -> Python executes -> Model answers)
- Hỗ trợ fallback cục bộ thông minh nếu không có API key
"""

import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from tools import TOOL_CATALOG
from data import load_clean_data, find_province_in_text, match_province

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MAX_TOOL_ROUNDS = 4

# Mỗi model chạy qua đúng nhà cung cấp của nó (tên model bắt đầu bằng "gemini" -> Google, còn lại -> OpenRouter)
PROVIDERS = {
    "gemini": {"label": "Google Gemini", "base_url": GEMINI_BASE_URL, "env": "GEMINI_API_KEY"},
    "openrouter": {"label": "OpenRouter", "base_url": OPENROUTER_BASE_URL, "env": "OPENROUTER_API_KEY"},
}

def get_provider(model: str) -> str:
    return "gemini" if str(model).lower().startswith("gemini") else "openrouter"


SYSTEM_PROMPT = """Bạn là HouseAssist, trợ lý AI chuyên nghiệp phân tích và định giá bất động sản tại thị trường Việt Nam.
Phạm vi chuyên môn: nhà ở tại các tỉnh/thành lớn như Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Bình Dương, Đồng Nai, Cần Thơ và toàn quốc.

Nhiệm vụ và Quy tắc ứng xử:
1. Thân thiện, ngắn gọn, súc tích và có tính học thuật chuyên sâu.
2. Sử dụng các công cụ (Tools) được cung cấp khi người dùng yêu cầu:
   - Dự đoán giá nhà (Tỷ VNĐ) -> Dùng 'predict_house_price'
   - Thống kê thị trường (trung vị, min, max, số lượng giao dịch) -> Dùng 'get_market_statistics'
   - Xác định phân khúc của một mức giá cụ thể -> Dùng 'segment_house'
   - Giải thích/so sánh 4 phân khúc (Bình dân, Trung cấp, Cao cấp, Hạng sang) -> Dùng 'explain_market_segments'
   - Tìm kiếm căn nhà tương đồng trong bộ dữ liệu -> Dùng 'find_similar_houses'
   - Giải thích các yếu tố tác động đến giá trị (Feature Importance) -> Dùng 'explain_price_factors'
3. Tuyệt đối không tự bịa đặt số liệu thống kê hoặc giá nhà khi chưa chạy công cụ.
4. Tận dụng ngữ cảnh hội thoại trước đó (Follow-up questions) để điền các tham số còn thiếu.
5. Nếu công cụ báo không nhận diện được tỉnh/thành, hãy hỏi lại khách, KHÔNG tự đổi sang tỉnh khác.
6. Khi báo giá dự đoán, nêu rõ đây là khoảng ước tính tham khảo (sai số trung bình khoảng 21%).
7. Trả lời bằng tiếng Việt chuyên nghiệp, định dạng số tiền rõ ràng (Tỷ VNĐ / triệu/m²), kèm nhận xét thực tế.

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

NGUYÊN TẮC KHI GỢI Ý NHÀ TƯƠNG ĐỒNG:
Khi khách hàng muốn tìm nhà, bạn BẮT BUỘC phải xác định rõ 3 thông tin từ chính lời khách nói: Tỉnh/Thành phố, Mức giá và Diện tích.
NẾU KHÁCH THIẾU BẤT KỲ THÔNG TIN NÀO TRONG 3 YÊU CẦU TRÊN (đặc biệt là Tỉnh/Thành phố hoặc Diện tích):
- TUYỆT ĐỐI KHÔNG tự ý suy diễn, nội suy hoặc bịa ra con số (như tự gán 80m2).
- KHÔNG ĐƯỢC PHÉP gọi công cụ 'find_similar_houses'.
- Bắt buộc phải dừng lại và nhắn tin hỏi khách để thu thập đủ thông tin. (Ví dụ: "Dạ với ngân sách 5 tỷ tại Hà Nội, anh/chị muốn tìm nhà có diện tích khoảng bao nhiêu m² ạ?")
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
                "required": ["land_area", "province"],
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
            "description": "Xác định phân khúc căn nhà (Bình dân / Trung cấp / Cao cấp / Hạng sang) tại một tỉnh/thành cụ thể.",
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
                    "province": {
                        "type": "string",
                        "description": "Tỉnh/Thành phố (ví dụ: Hà Nội, Đà Nẵng).",
                    },
                },
                "required": ["price_billion_vnd"],
            },
        },
    },
        {
        "type": "function",
        "function": {
            "name": "explain_market_segments",
            "description": "Mô tả 4 phân khúc thị trường (Bình dân, Trung cấp, Cao cấp, Hạng sang) bằng số liệu thật: tỷ trọng, giá trung vị, diện tích, loại nhà phổ biến.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_houses",
            "description": "Tìm kiếm các ngôi nhà tương đồng trong kho hàng thực tế dựa trên yêu cầu của khách.",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "Tên tỉnh/thành phố khách hàng muốn tìm (Ví dụ: 'Hà Nội', 'Đà Nẵng'). Bắt buộc phải có."
                    },
                    "price_billion": {
                        "type": "number",
                        "description": "Mức giá mong muốn tính bằng tỷ VNĐ. Bắt buộc phải có."
                    },
                    "land_area": {
                        "type": "number",
                        "description": "Diện tích mong muốn tính bằng m2. Bắt buộc phải có."
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Số lượng phòng ngủ mong muốn. (Không bắt buộc)"
                    },
                    "property_type": {
                        "type": "string",
                        "description": "Loại hình bất động sản (Ví dụ: 'Chung cư', 'Nhà phố'). (Không bắt buộc)"
                    }
                },
                # Khóa chặt 3 tham số này, nếu LLM thấy thiếu nó sẽ tự động hỏi lại khách
                "required": ["province", "price_billion", "land_area"]
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
    Thực thi 1 lượt phản hồi của Agent với đầy đủ chu trình Tool Calling (tối đa MAX_TOOL_ROUNDS vòng).
    Trả về: (câu trả lời cuối cùng, danh sách các tool calls đã diễn ra).
    """
    provider = PROVIDERS[get_provider(model)]
    if not api_key:
        api_key = os.getenv(provider["env"], "")

    full_messages = []
    if not messages or messages[0].get("role") != "system":
        full_messages.append({"role": "system", "content": SYSTEM_PROMPT})
    full_messages.extend(messages)

    tool_logs = []

    # Không có API key -> bộ điều phối offline
    if not api_key:
        return _run_heuristic_fallback(messages[-1]["content"])

    headers = {"HTTP-Referer": site_url, "X-Title": site_name} if provider is PROVIDERS["openrouter"] else None
    client = OpenAI(base_url=provider["base_url"], api_key=api_key, default_headers=headers)

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=model,
                messages=full_messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or "Tôi có thể hỗ trợ gì thêm về thị trường bất động sản Việt Nam?", tool_logs

            # Ghi lại yêu cầu gọi công cụ (dạng dict chuẩn OpenAI để mọi nhà cung cấp đều nhận)
            full_messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    fn_args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    fn_args = {}
                tool_result = execute_tool_call(tc.function.name, fn_args)
                tool_logs.append({"tool_name": tc.function.name, "arguments": fn_args, "result": tool_result})
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

        # Hết số vòng: yêu cầu mô hình tổng hợp, không cho gọi thêm công cụ
        final = client.chat.completions.create(model=model, messages=full_messages, temperature=0.3)
        return final.choices[0].message.content or "", tool_logs

    except Exception as e:
        fallback_ans, fallback_tools = _run_heuristic_fallback(messages[-1]["content"])
        note = f"\n\n*(Lưu ý: đã chuyển sang chế độ phân tích ngoại tuyến vì kết nối {provider['label']} gặp lỗi: {str(e)[:100]})*"
        return fallback_ans + note, fallback_tools


# ------------------------------------------------------------------------------
# CHẾ ĐỘ OFFLINE: trích tham số từ câu hỏi, KHÔNG tự bịa giá trị còn thiếu
# ------------------------------------------------------------------------------
_NUM = r"(\d+(?:[.,]\d+)?)"
_PROPERTY_KEYWORDS = {
    "nhà phố": "Nhà phố", "chung cư": "Chung cư", "biệt thự": "Biệt thự",
    "nhà cấp 4": "Nhà cấp 4", "liền kề": "Nhà liền kề",
}

def _to_float(s):
    return float(str(s).replace(",", "."))

def _extract_params(text: str, provinces: list) -> dict:
    t = text.lower()
    price = re.search(_NUM + r"\s*(?:tỷ|tỉ|ty)", t)
    area = re.search(_NUM + r"\s*(?:m2|m²|mét vuông|m\b)", t)
    beds = re.search(r"(\d+)\s*(?:pn|phòng ngủ)", t)
    baths = re.search(r"(\d+)\s*(?:wc|phòng tắm)", t)
    floors = re.search(r"(\d+)\s*tầng", t)
    return {
        "province": find_province_in_text(text, provinces),
        "price": _to_float(price.group(1)) if price else None,
        "area": _to_float(area.group(1)) if area else None,
        "bedrooms": int(beds.group(1)) if beds else None,
        "bathrooms": float(baths.group(1)) if baths else None,
        "floors": float(floors.group(1)) if floors else None,
        "property_type": next((v for k, v in _PROPERTY_KEYWORDS.items() if k in t), None),
    }

def _log(tool_logs, name, args, result):
    tool_logs.append({"tool_name": name, "arguments": args, "result": result})
    return result

def _run_heuristic_fallback(user_text: str) -> tuple[str, list]:
    """Điều phối cục bộ khi không có API. Thiếu thông tin bắt buộc thì hỏi lại khách, không dùng giá trị mặc định."""
    t = user_text.lower()
    tool_logs = []
    provinces = load_clean_data()["Province"].unique().tolist()
    p = _extract_params(user_text, provinces)
    has = lambda words: any(w in t for w in words)

    # 1. Yếu tố chi phối giá
    if has(["yếu tố", "quan trọng", "ảnh hưởng", "feature importance", "tại sao giá", "tác động", "chi phối"]):
        res = _log(tool_logs, "explain_price_factors", {}, TOOL_CATALOG["explain_price_factors"]())
        ans = "### Các yếu tố chi phối giá nhà (Random Forest)\n"
        ans += "".join(f"- {s}\n" for s in res.get("key_market_takeaways", []))
        ans += "\n**Tỷ lệ quan trọng:**\n"
        for k, v in list(res.get("top_factors_importance_share", {}).items())[:5]:
            ans += f"- {k}: {v*100:.1f}%\n"
        return ans, tool_logs

    # 2. Phân khúc: có giá cụ thể -> xác định phân khúc; không có -> giải thích 4 phân khúc
    if has(["phân khúc", "segment"]):
        if p["price"] is not None:
            args = {"price_billion_vnd": p["price"], "province": p["province"], "land_area_m2": p["area"]}
            res = _log(tool_logs, "segment_house", args, TOOL_CATALOG["segment_house"](**args))
            ans = "### Phân khúc theo ngưỡng giá\n"
            ans += f"- **Phân khúc:** {res['segment_name']}\n- **Mức giá:** {res['price_analyzed']}\n- {res['market_profile']}\n"
            if res.get("local_position"):
                ans += f"- {res['local_position']}\n"
            return ans, tool_logs
        res = _log(tool_logs, "explain_market_segments", {}, TOOL_CATALOG["explain_market_segments"]())
        ans = f"### 4 phân khúc thị trường\n{res['definition']}\n"
        for s in res["segments"]:
            ans += (f"\n**{s['name']}**: {s['share_pct']}% số tin, giá trung vị {s['median_price']} tỷ, "
                    f"đất TB {s['mean_land_area']:.0f} m², {s['median_bedrooms']} PN, {s['median_floors']} tầng, "
                    f"phổ biến nhất: {s['top_property_type']} ({s['top_property_share_pct']:.0f}%).\n")
        return ans, tool_logs

    # 3. Tìm nhà tương đồng: bắt buộc đủ tỉnh, giá, diện tích
    if has(["tìm nhà", "tìm giúp", "tìm kiếm", "tìm căn", "tương đồng", "tương tự", "find"]):
        missing = [n for n, k in [("Tỉnh/Thành phố", "province"), ("mức giá (tỷ)", "price"), ("diện tích (m²)", "area")] if p[k] is None]
        if missing:
            return f"Để tìm nhà phù hợp, anh/chị vui lòng cho biết thêm: **{', '.join(missing)}** ạ.", tool_logs
        args = {"province": p["province"], "price_billion": p["price"], "land_area": p["area"], "limit": 3}
        res = _log(tool_logs, "find_similar_houses", args, TOOL_CATALOG["find_similar_houses"](**args))
        if res.get("status") != "success":
            return f"Không tìm thấy dữ liệu: {res.get('message', 'Không xác định')}", tool_logs
        ans = f"### Nhà tương đồng ({p['price']} tỷ, {p['area']:.0f} m², {p['province']})\n"
        for i, h in enumerate(res["recommendations"], 1):
            ans += (f"{i}. **{h['Loại nhà']}** tại {h['Địa chỉ']}: {h['Giá bán (Tỷ)']} tỷ, "
                    f"{h['Diện tích (m2)']} m², {h['Phòng ngủ']} PN (độ lệch {h['Độ sai lệch']})\n")
        return ans, tool_logs

    # 4. Dự đoán giá: bắt buộc có diện tích và tỉnh/thành
    if has(["dự đoán", "định giá", "ước tính", "predict"]):
        missing = [n for n, k in [("Tỉnh/Thành phố", "province"), ("diện tích đất (m²)", "area")] if p[k] is None]
        if missing:
            return f"Để định giá, anh/chị vui lòng cho biết thêm: **{', '.join(missing)}** ạ.", tool_logs
        args = {k: v for k, v in {
            "land_area": p["area"], "province": p["province"], "bedrooms": p["bedrooms"],
            "bathrooms": p["bathrooms"], "floors": p["floors"], "property_type": p["property_type"],
        }.items() if v is not None}
        res = _log(tool_logs, "predict_house_price", args, TOOL_CATALOG["predict_house_price"](**args))
        if res.get("status") != "success":
            return f"Không định giá được: {res.get('message', 'Không xác định')}", tool_logs
        s = res["input_summary"]
        ans = "### Ước tính giá (Random Forest)\n"
        ans += f"- **Giá dự đoán:** {res['estimated_price_formatted']}\n"
        ans += f"- **Khoảng 80%:** {res['price_range_formatted']}\n- **Đơn giá:** {res['price_per_m2_formatted']}\n"
        ans += f"- **Căn nhà:** {s['property_type']} {s['land_area_m2']:.0f} m², {s['bedrooms']} PN, {s['bathrooms']:.0f} WC tại {s['province']}\n"
        ans += f"\n*{res['note']}*"
        return ans, tool_logs

    # 5. Thống kê thị trường
    if has(["thống kê", "trung vị", "trung bình", "median", "bao nhiêu căn", "tổng số", "thị trường", "market"]):
        args = {"province": p["province"]}
        res = _log(tool_logs, "get_market_statistics", args, TOOL_CATALOG["get_market_statistics"](**args))
        ans = f"### Thống kê thị trường ({res.get('scope', 'Việt Nam')})\n"
        ans += f"- **Số tin:** {res.get('total_listings', 0):,}\n- **Giá trung vị:** {res.get('median_price_formatted', 'N/A')}\n"
        ans += f"- **Giá trung bình:** {res.get('mean_price_formatted', 'N/A')}\n- **Đơn giá TB:** {res.get('avg_price_per_m2', 'N/A')}\n"
        for key, title in [("top_5_expensive_provinces", "Top 5 đắt nhất"), ("top_5_affordable_provinces", "Top 5 dễ tiếp cận nhất")]:
            if key in res:
                ans += f"\n**{title}:**\n" + "".join(f"- {k}: {v}\n" for k, v in res[key].items())
        return ans, tool_logs

    # 6. Không hiểu ý: gợi ý cách hỏi, không tự chạy công cụ
    return ("Chế độ ngoại tuyến hiện hỗ trợ: **thống kê thị trường** (VD: \"thống kê Hà Nội\"), "
            "**định giá** (VD: \"định giá nhà phố 80 m², 3 PN tại Đà Nẵng\"), **phân khúc**, **tìm nhà tương đồng** "
            "và **yếu tố ảnh hưởng giá**. Anh/chị thử hỏi theo các mẫu này nhé."), tool_logs
