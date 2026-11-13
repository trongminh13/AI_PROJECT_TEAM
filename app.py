"""
Ứng dụng: app.py
Giao diện Web Streamlit cho HouseAssist - AI Real Estate Advisor & Analytics Agent
Thiết kế theo chuẩn mực Cao cấp, Thơ mộng & Sang trọng (Poetic Atmospheric Luxury):
- Nút bấm góc vuông sắc sảo (border-radius: 0px), phóng to nhẹ khi hover kèm viền xanh lam chuyển động loop neon.
- Cấu hình LLM & API được tách biệt gọn gàng vào Tab Cài Đặt (Settings).
- Luồng cuộn trang dọc (Vertical Scroll Flow): Khám phá thị trường 4 phân khúc K-Means, Lăng kính đô thị và Biểu đồ định giá.
"""

import os
import base64
import html
import json
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import pandas as pd
from agent import run_agent_turn, DEFAULT_MODEL, PROVIDERS, get_provider
from data import load_listing_data, get_trained_models, get_model_report, segment_table, FEATURE_LABELS
from tools import get_market_statistics, segment_house
from shoji_view import get_shoji_html
from scroll_view import get_scroll_styles, get_single_scroll_html, SCROLL_ITEMS

# Cấu hình trang giao diện
st.set_page_config(
    page_title="HouseAssist • AI Real Estate Advisor",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# QUẢN TRỊ TRẠNG THÁI VIDEO BACKGROUND & CACHE
# ==============================================================================
if "enable_video_bg" not in st.session_state:
    st.session_state.enable_video_bg = True
if "bg_blur" not in st.session_state:
    st.session_state.bg_blur = 12   # Tăng độ mờ (blur) lên 12 để làm nhòe phông nền
if "bg_darkness" not in st.session_state:
    st.session_state.bg_darkness = 60  # Tăng độ tối lên 60% để tạo độ sâu

@st.cache_data
def get_ambient_video_b64(video_path: str = "assets/ambient_bg.mp4") -> str:
    """Nạp video và cache chuỗi base64 trong bộ nhớ RAM, tránh đọc lại đĩa khi tương tác."""
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def render_tool_output(data: dict) -> None:
    """Hiển thị dữ liệu tool trong khung cuộn dùng font chuẩn lập trình (Monospace)."""
    formatted_json = html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    component_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: transparent; color: #E2E8F0; }}
.output {{ height: 310px; overflow: auto; padding: 14px 16px; border: 1px solid rgba(183,157,114,.35); border-radius: 8px; background: rgba(7,11,25,.78); }}
pre {{ margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font-family: Consolas, "Courier New", monospace; font-size: 14px; line-height: 1.65; color: #38BDF8; }}
</style></head><body><div class="output"><pre>{formatted_json}</pre></div></body></html>"""
    st.iframe(src=component_html, height=330, width="stretch")

# Khởi tạo markup cho video background nếu được kích hoạt
video_canvas_html = ""
app_bg_css = ""
if st.session_state.enable_video_bg:
    b64_vid = get_ambient_video_b64()
    if b64_vid:
        blur_val = st.session_state.bg_blur
        dark_ratio = st.session_state.bg_darkness / 100.0
        # Lớp phủ voan tối mỏng nhẹ để cảnh video sáng rõ, chỉ mờ tí xíu
        c1 = f"rgba(3, 7, 18, {dark_ratio * 0.35:.2f})"
        c2 = f"rgba(7, 11, 25, {dark_ratio * 0.55:.2f})"
        c3 = f"rgba(3, 7, 18, {min(0.85, dark_ratio * 0.85):.2f})"
        video_canvas_html = f"""
        <div class="ambient-video-wrapper">
            <video class="ambient-video" autoplay loop muted playsinline>
                <source src="data:video/mp4;base64,{b64_vid}" type="video/mp4">
            </video>
            <div class="ambient-overlay" style="
                backdrop-filter: blur({blur_val}px);
                -webkit-backdrop-filter: blur({blur_val}px);
                background: radial-gradient(ellipse at 50% 30%, {c1} 0%, {c2} 55%, {c3} 100%);
            "></div>
        </div>
        """
        app_bg_css = ".stApp { background: transparent !important; }"

if not app_bg_css:
    app_bg_css = ".stApp { background: radial-gradient(circle at 15% 15%, #0B132B 0%, #070B19 50%, #030712 100%) !important; }"

# ==============================================================================
# BỘ CSS NGHỆ THUẬT: POETIC ATMOSPHERIC LUXURY & ANIMATED BUTTON BORDER
# ==============================================================================
st.markdown(
    f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <!-- THÊM &subset=vietnamese ĐỂ KHÔNG BỊ LỖI DẤU TIẾNG VIỆT, BỎ FONT MỎNG 300 ĐI -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap&subset=vietnamese" rel="stylesheet">

    <style>
    /* Reset & Typography */
    html, body, [class*="css"] {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #FFFFFF !important; /* ĐỔI SANG MÀU TRẮNG TINH 100% */
        font-weight: 500 !important; /* TĂNG ĐỘ ĐẬM CỦA CHỮ LÊN MỨC MEDIUM */
        text-shadow: 0px 1px 3px rgba(0,0,0,0.5); /* THÊM BÓNG ĐỔ ĐEN NHẸ ĐỂ CHỮ NỔI LÊN NỀN SÁNG */
    }}

    /* Nền ứng dụng (Động trong suốt khi bật video nền, Tĩnh khi tắt) */
    {app_bg_css}

    /* Hệ thống Video Background Cố Định Toàn Màn Hình */
    .ambient-video-wrapper {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: -9999 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }}

    .ambient-video {{
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        min-width: 100% !important;
        min-height: 100% !important;
        width: auto !important;
        height: auto !important;
        transform: translate(-50%, -50%) translate3d(0, 0, 0) !important;
        object-fit: cover !important;
        will-change: transform !important;
    }}

    .ambient-overlay {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
    }}

    /* Triệt tiêu hoàn toàn khoảng gap trên đỉnh của stMainBlockContainer, block-container và header */
    header[data-testid="stHeader"],
    header.stAppHeader,
    [data-testid="stHeader"] {{
        background: transparent !important;
        height: 0px !important;
        min-height: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    [data-testid="stToolbar"],
    .stAppToolbar {{
        top: 0.2rem !important;
        right: 0.5rem !important;
        z-index: 9999 !important;
    }}

    /* Nhắm mục tiêu chính xác vào stMainBlockContainer, block-container và toàn bộ biến thể */
    .stMainBlockContainer,
    .block-container,
    [data-testid="stMainBlockContainer"],
    div.stMainBlockContainer,
    div.block-container,
    div[class*="stMainBlockContainer"],
    div[class*="block-container"],
    .eqt0gmo4 {{
        padding-top: 0.2rem !important;
        padding-bottom: 2rem !important;
        margin-top: 0px !important;
        max-width: 1420px !important;
    }}

    /* Triệt tiêu margin-top của khối con đầu tiên và Tabs */
    .stMainBlockContainer > div:first-child,
    .block-container > div:first-child,
    [data-testid="stVerticalBlock"]:first-child,
    .stTabs {{
        margin-top: 0px !important;
        padding-top: 0px !important;
    }}

    /* Tiêu đề thơ mộng phong cách Editorial */
    .hero-title {{
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #000000 !important; /* Đen tuyền sắc nét */
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
        /* Triệt tiêu bóng viền, thay bằng hào quang sáng mờ 360 độ phía sau chữ */
        text-shadow: 0 0 25px rgba(255, 255, 255, 1) !important;
    }}

    .hero-subtitle {{
        font-size: 1.15rem;
        color: #F8FAFC !important;
        font-weight: 400;
        line-height: 1.6;
        margin-bottom: 1.2rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
    }}

    /* ==========================================================================
       HỆ THỐNG NÚT BẤM GÓC VUÔNG & VIỀN XANH LAM CHUYỂN ĐỘNG LOOP
       ========================================================================== */
    div.stButton > button {{
        border-radius: 0px !important;
        position: relative !important;
        background-color: #0B132B !important;
        color: #F8FAFC !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.3px !important;
        border: 2px solid #1E293B !important;
        padding: 0.65rem 0.75rem !important;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease !important;
        overflow: hidden !important;
    }}

    /* Khi hover: Phóng to 1 chút và viền xanh lam chuyển động loop vòng quanh */
    div.stButton > button:hover {{
        transform: scale(1.045) !important;
        border-color: transparent !important;
        background-image: linear-gradient(#0B132B, #0B132B), 
                          linear-gradient(90deg, #00F0FF, #0055FF, #00F0FF, #38BDF8, #00F0FF) !important;
        background-origin: padding-box, border-box !important;
        background-clip: padding-box, border-box !important;
        background-size: 100% 100%, 300% 100% !important;
        animation: borderLoopFlow 2s linear infinite !important;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.45) !important;
        color: #FFFFFF !important;
    }}

    /* Keyframes chuyển động viền loop tuần hoàn */
    @keyframes borderLoopFlow {{
        0% {{ background-position: 0 0, 0% 0; }}
        100% {{ background-position: 0 0, 300% 0; }}
    }}

    /* Tin nhắn hội thoại Glassmorphism trong trẻo đón video nền sắc nét */
    [data-testid="stChatMessage"] {{
        background: rgba(11, 19, 43, 0.40) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(56, 189, 248, 0.22) !important;
        border-radius: 0px !important;
        padding: 1.1rem 1.25rem !important;
        margin-bottom: 0.9rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
    }}

    /* ==========================================================================
       KHUNG NHẬP LIỆU CHAT INPUT GỖ ẤM SHOJI (ZEN COMMAND CENTER)
       ========================================================================== */
    /* Container bên ngoài của ô nhập: Màu nâu gỗ Trà Thất Shoji, viền Kumiko, bo góc 24px */
    [data-testid="stChatInput"] > div {{
        border-radius: 24px !important;
        background: rgba(45, 29, 18, 0.88) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 3px solid #5a3d24 !important;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.85), 0 0 25px rgba(185, 159, 104, 0.22) !important;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 0.8rem 1.3rem !important;
        min-height: 105px !important;
        display: flex !important;
        align-items: center !important;
    }}

    /* Khi di chuột hoặc focus: Viền sáng ánh vàng đồng thau / Kumiko ấm áp */
    [data-testid="stChatInput"] > div:hover,
    [data-testid="stChatInput"] > div:focus-within {{
        border-color: #d4b27a !important;
        border-width: 3px !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.9), 0 0 35px rgba(212, 178, 122, 0.45), inset 0 0 15px rgba(212, 178, 122, 0.15) !important;
        transform: translateY(-2px) !important;
    }}

    /* Khung hình chữ nhật bên trong bo góc (BaseWeb input wrapper) */
    [data-testid="stChatInput"] [data-baseweb="base-input"],
    [data-testid="stChatInput"] [data-baseweb="input"],
    [data-testid="stChatInput"] div[class*="stChatInputTextArea"] {{
        border-radius: 16px !important;
        overflow: hidden !important;
        background: rgba(28, 18, 11, 0.70) !important;
        border: 1.5px solid rgba(138, 106, 62, 0.35) !important;
        transition: border-color 0.3s ease, background 0.3s ease !important;
    }}

    [data-testid="stChatInput"] > div:focus-within [data-baseweb="base-input"] {{
        border-color: rgba(212, 178, 122, 0.65) !important;
        background: rgba(28, 18, 11, 0.88) !important;
    }}

    /* Thẻ nhập chữ (Textarea) bên trong khung chữ nhật bo góc, CHỮ TRẮNG TINH 100% */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"],
    [data-testid="stChatInput"] textarea:focus {{
        border-radius: 14px !important;
        background: transparent !important;
        border: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #d4b27a !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 500 !important;
        line-height: 1.7 !important;
        min-height: 75px !important;
        padding: 0.5rem 0.7rem !important;
    }}

    /* Placeholder chữ trắng sáng ngà thư thái */
    [data-testid="stChatInput"] textarea::placeholder {{
        color: rgba(246, 237, 216, 0.85) !important;
        -webkit-text-fill-color: rgba(246, 237, 216, 0.85) !important;
        font-size: 1.12rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
    }}

    /* Nút gửi (Send button): gradient vàng đồng & gỗ ấm Trà Thất */
    [data-testid="stChatInput"] button {{
        border-radius: 16px !important;
        background: linear-gradient(135deg, #d4b27a 0%, #8b6a45 50%, #5a3d24 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        width: 56px !important;
        height: 56px !important;
        align-self: center !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
        cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }}

    [data-testid="stChatInput"] button:hover {{
        transform: scale(1.08) !important;
        box-shadow: 0 0 25px rgba(212, 178, 122, 0.75), 0 0 15px #8b6a45 !important;
    }}

    [data-testid="stChatInput"] button svg {{
        width: 26px !important;
        height: 26px !important;
        fill: #FFFFFF !important;
    }}

    /* Card thông số cuộn bên dưới kính mờ phản quang */
    .feature-card {{
        background: rgba(11, 19, 43, 0.40);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 0px;
        padding: 1.5rem;
        height: 100%;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }}
    .feature-card:hover {{
        transform: translateY(-4px);
        border-color: #00F0FF;
        box-shadow: 0 8px 30px rgba(0, 240, 255, 0.25);
    }}
    .card-tag {{
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #38BDF8;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    .card-val {{
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.4rem;
    }}
    .card-desc {{
        font-size: 0.95rem;
        color: #E2E8F0 !important;
        line-height: 1.5;
    }}

    /* Tab navigation thanh thoát, chữ trắng ngà sáng rõ */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1.5rem;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important;
        padding: 0.8rem 1rem !important;
        border-radius: 0px !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: #00F0FF !important;
        border-bottom: 2px solid #00F0FF !important;
    }}

    /* Trắng hóa toàn diện các thẻ caption và đoạn văn bản trên nền tối */
    .stCaption, [data-testid="stCaptionContainer"] p, [data-testid="stMarkdownContainer"] p {{
        color: #F8FAFC !important;
    }}

    /* ==========================================================================
       SIDEBAR TRONG SUỐT HIỂN THỊ VIDEO NỀN & CẠNH NGĂN CÁCH BÓNG MỜ HÀO QUANG
       ========================================================================== */
    [data-testid="stSidebar"] {{
        background: rgba(7, 11, 25, 0.20) !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
        border-right: 2px solid rgba(0, 240, 255, 0.5) !important;
        box-shadow: 20px 0 50px rgba(0, 0, 0, 0.9), 8px 0 25px rgba(0, 240, 255, 0.35), 2px 0 10px rgba(0, 240, 255, 0.6) !important;
    }}

    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background: transparent !important;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: rgba(56, 189, 248, 0.28) !important;
    }}

    /* Nút mở Sidebar khi bị thu gọn: Sáng rõ, dễ nhận diện */
    [data-testid="stSidebarCollapsedControl"] {{
        color: #00F0FF !important;
        background: rgba(11, 19, 43, 0.85) !important;
        border: 1.5px solid rgba(0, 240, 255, 0.5) !important;
        border-radius: 8px !important;
        margin: 0.5rem !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3) !important;
    }}
    [data-testid="stSidebarCollapsedControl"]:hover {{
        background: #00F0FF !important;
        color: #0B132B !important;
        box-shadow: 0 0 25px #00F0FF !important;
    }}

    /* --- BỘ CODE CHUYÊN TRỊ ST.BOTTOM MỚI NHẤT --- */
    
    /* Tắt tính năng Neo Đáy của Streamlit */
    div[data-testid="stBottom"] {{
        position: static !important;
        background: transparent !important;
        padding-bottom: 0px !important;
        display: block !important;
    }}
    
    /* Cho khung Chat trôi tự do trong cột của nó */
    div[data-testid="stBottom"] > div {{
        display: block !important;
        background: transparent !important;
        position: relative !important;
    }}

    /* Chỉnh kích thước và kéo khung chat sát vào cửa gỗ */
    div[data-testid="stChatInput"] {{
        width: 100% !important; /* Dùng 100% chiều rộng của cột bên trái */
        max-width: 960px !important;
        margin: -25px auto 1rem auto !important; /* Lên nhẹ 25px */
        position: relative !important;
        z-index: 999999 !important;
    }}

    /* 1. Sửa màu chữ Top 3 khu vực đắt nhất trong Sidebar thành màu trắng rõ nét */
    [data-testid="stSidebar"] li, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div {{
        color: #FFFFFF !important;
    }}

    /* 2. Sửa khung Expander / Lịch sử trò chuyện thành nền tối sang trọng */
    div[data-testid="stExpander"] {{
        background: rgba(11, 19, 43, 0.85) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 8px !important;
    }}
    
    /* Chữ bên NGOÀI (Tiêu đề, Bạn:, Chi tiết công cụ) -> Màu trắng sáng */
    div[data-testid="stExpander"] p, 
    div[data-testid="stExpander"] span, 
    div[data-testid="stExpander"] li, 
    div[data-testid="stExpander"] div,
    div[data-testid="stExpander"] h1,
    div[data-testid="stExpander"] h2,
    div[data-testid="stExpander"] h3,
    div[data-testid="stExpander"] h4,
    div[data-testid="stExpander"] h5 {{
        color: #F1F5F9 !important;
    }}

    /* ĐÈ LẠI: Chữ bên TRONG ô thông báo màu sáng (st.info) -> Màu đen sắc nét */
    div[data-testid="stExpander"] [data-testid="stAlert"] p,
    div[data-testid="stExpander"] [data-testid="stAlert"] span,
    div[data-testid="stExpander"] [data-testid="stAlert"] div,
    div[data-testid="stExpander"] [data-testid="stAlert"] strong,
    div[data-testid="stExpander"] [data-testid="stAlert"] li,
    div[data-testid="stExpander"] [data-testid="stAlert"] ul,
    div[data-testid="stExpander"] [data-testid="stAlert"] ol {{
        color: #0F172A !important; 
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# Chèn Video Background vào DOM nếu bật
if video_canvas_html:
    st.markdown(video_canvas_html, unsafe_allow_html=True)

# Khởi tạo session state lưu câu hỏi, câu trả lời Shoji và cấu hình
if "shoji_q" not in st.session_state:
    st.session_state.shoji_q = ""
if "shoji_a" not in st.session_state:
    st.session_state.shoji_a = ""
if "last_tools" not in st.session_state:
    st.session_state.last_tools = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Cấu hình API key mặc định: mỗi nhà cung cấp (Gemini / OpenRouter) một khóa riêng
if "api_keys" not in st.session_state:
    _keys = {}
    for _pid, _cfg in PROVIDERS.items():
        _key = os.getenv(_cfg["env"], "")
        if not _key:
            try:
                _key = st.secrets.get(_cfg["env"], "")
            except Exception:
                _key = ""
        _keys[_pid] = _key
    st.session_state.api_keys = _keys

if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL


def current_provider() -> str:
    return get_provider(st.session_state.selected_model)


def current_api_key() -> str:
    return st.session_state.api_keys.get(current_provider(), "")

# ==============================================================================
# THANH SIDEBAR BÊN TRÁI (LEFT SIDEBAR DASHBOARD & CONTROLS)
# ==============================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #FFFFFF; line-height: 1.2;">
            🏡 HouseAssist
        </div>
        <div style="font-size: 0.8rem; color: #38BDF8; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 1rem; font-weight: 600;">
            Vietnam Real Estate AI
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Trạng thái kết nối LLM
    if current_api_key():
        st.markdown(
            """
            <div style="padding: 6px 12px; background: rgba(16, 185, 129, 0.15); border-left: 3px solid #10B981; margin-bottom: 1rem;">
                <span style="color: #10B981; font-weight: 600; font-size: 0.85rem;">🟢 Online (""" + PROVIDERS[current_provider()]["label"] + """)</span><br>
                <span style="color: #94A3B8; font-size: 0.75rem;">Model: """
            + str(st.session_state.selected_model)
            + """</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="padding: 6px 12px; background: rgba(245, 158, 11, 0.15); border-left: 3px solid #F59E0B; margin-bottom: 1rem;">
                <span style="color: #F59E0B; font-weight: 600; font-size: 0.85rem;">🟡 Chế độ Nội Bộ (Offline)</span><br>
                <span style="color: #94A3B8; font-size: 0.75rem;">Chạy bộ điều phối Heuristic</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Nút Reset hội thoại góc vuông với viền neon loop
    if st.button("🔄 Làm Mới Hội Thoại", width="stretch"):
        st.session_state.chat_history = []
        st.session_state.shoji_q = ""
        st.session_state.shoji_a = ""
        st.session_state.last_tools = []
        st.rerun()

    st.markdown("---")

    # Bảng chỉ số thị trường nhanh
    st.markdown("### 📊 Chỉ Số Thị Trường")
    try:
        df_side = load_listing_data()
        sb_c1, sb_c2 = st.columns(2)
        with sb_c1:
            st.metric("Giao dịch", f"{len(df_side):,}")
            st.metric("Đơn giá TB", f"{df_side['price_per_m2'].mean():.1f} tr/m²")
        with sb_c2:
            st.metric("Giá trung vị", f"{df_side['Price_Billion_VND'].median():.2f} tỷ")
            st.metric("Diện tích TB", f"{df_side['Land_Area'].mean():.0f} m²")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💎 **Top 3 khu vực đắt nhất:**")
        top3 = df_side.groupby("Province")["Price_Billion_VND"].median().sort_values(ascending=False).head(3)
        for prov_name, val in top3.items():
            st.markdown(f"- **{prov_name}:** `{val:.2f} tỷ VNĐ`")
    except Exception as e:
        st.warning(f"Chưa nạp được dữ liệu: {e}")

    st.markdown("---")
    st.caption("💡 *Bạn có thể cấu hình chi tiết API Key tại Tab **Cài Đặt Hệ Thống**.*")
    st.caption("🎓 *Jetking ADAI • Semester 1 Capstone Project*")

# ==============================================================================
# HỆ THỐNG ĐIỀU HƯỚNG TABS
# ==============================================================================
main_tab, explore_tab, settings_tab = st.tabs(
    [
        "⛩️ Trà Thất AI (Định Giá & Hội Thoại)",
        "📊 Toàn Cảnh Thị Trường",
        "⚙️ Cài Đặt Hệ Thống",
    ]
)

# ==============================================================================
# TAB 1: KHÔNG GIAN THIỀN ĐỊNH SHOJI & TRÒ CHUYỆN ĐỊNH GIÁ (CHỦ ĐẠO)
# ==============================================================================
with main_tab:
    # Header thơ mộng
    st.markdown('<div class="hero-title">HouseAssist • Trà Thất AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Hệ thống Trí tuệ Nhân tạo Phân tích, Định giá & Khám phá Bất động sản Việt Nam qua Không gian Thiền Định Shoji.</div>',
        unsafe_allow_html=True,
    )

    # BỐ CỤC 2 CỘT: KHUNG TRÀ THẤT TO RỘNG (BÊN TRÁI) - CỤM CUỘN THƯ CỔ XƯA SÁT BÊN PHẢI
    shoji_col, quick_col = st.columns([4.1, 1.35], gap="medium")
    quick_prompt = None


    with shoji_col:
        # 1. Container cho toàn bộ khu vực bên trái (Trà Thất + Chat)
        st.markdown('<div class="zen-container">', unsafe_allow_html=True)
        
        # 2. Render khung Trà Thất Shoji
        shoji_markup = get_shoji_html(st.session_state.shoji_q, st.session_state.shoji_a)
        st.iframe(src=shoji_markup, height=500, width="stretch")
        
        # 3. Tạo một khoảng đệm mỏng
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        # 4. Đặt Chat Input thẳng vào cùng cột với Trà Thất (Streamlit sẽ tự động đẩy xuống dưới)
        user_input = st.chat_input("✨ Đặt câu hỏi cho Trà Thất Shoji về định giá, phân khúc, vị trí hoặc tìm nhà...")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with quick_col:
        # Tiêu đề & CSS toàn diện cho 4 cuộn thư cổ xưa kết hợp Native Button Overlay
        st.markdown(get_scroll_styles(), unsafe_allow_html=True)
        st.markdown(
            """
            <div class="scroll-header-block">
                <h3>🍵 Cuộn Thư Trà Thất</h3>
                <p>Rê chuột mở thư • Chạm để giải đáp</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 Hàng Cuộn Thư cổ xưa kết hợp nút Streamlit Native Button Overlay (Zero-Reload 100%)
        for idx, item in enumerate(SCROLL_ITEMS):
            unit_box = st.container()
            with unit_box:
                # Lớp 1: Giao diện cuộn thư cổ xưa
                st.markdown(get_single_scroll_html(item), unsafe_allow_html=True)
                # Lớp 2: Nút bấm Streamlit native phủ lên trên (vô hình, hứng click native qua WebSocket)
                if st.button(item["label"], key=f"overlay_scroll_btn_{idx}"):
                    quick_prompt = item["prompt"]

    active_prompt = quick_prompt or user_input

    if active_prompt:
        with st.spinner("Người trong Trà Thất Shoji đang mở sổ sách & kích hoạt mô hình AI..."):
            
            # CẤP TRÍ NHỚ (STATEFUL MEMORY) CHO HỆ THỐNG
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
                
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            
            # CHẠY AGENT ORCHESTRATOR
            response_text, tools_executed = run_agent_turn(
                messages=st.session_state.chat_history,
                api_key=current_api_key(),
                model=st.session_state.selected_model,
            )
            
            # LƯU KẾT QUẢ VÀO TRÍ NHỚ
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            
            # Cập nhật trực tiếp vào Khung Trà Thất Shoji duy nhất và rerun
            st.session_state.shoji_q = active_prompt
            st.session_state.shoji_a = response_text
            st.session_state.last_tools = tools_executed
            st.rerun()

    # Expander xem bản chép văn bản, lịch sử hội thoại & chi tiết công cụ ML
    if st.session_state.get("shoji_a"):
        with st.expander("📜 Cuộn Log Lịch Sử Hội Thoại & Phân Tích Công Cụ", expanded=False):
            st.markdown("### 🗂️ Lịch Sử Trò Chuyện (Chat History)")
            
            # Quét và in ra toàn bộ lịch sử trong chat_history
            if "chat_history" in st.session_state and len(st.session_state.chat_history) > 0:
                for idx, msg in enumerate(st.session_state.chat_history):
                    if msg["role"] == "user":
                        st.markdown(f"**👤 Bạn:** {msg['content']}")
                    elif msg["role"] == "assistant":
                        st.info(f"**🤖 Trà Thất Shoji:**\n\n{msg['content']}")
                        st.markdown("---")
            else:
                st.markdown(f"**👤 Bạn:** {st.session_state.shoji_q}")
                st.info(f"**🤖 Trà Thất Shoji:**\n\n{st.session_state.shoji_a}")
                st.markdown("---")
            
            # Hiển thị Tool của lượt tương tác CUỐI CÙNG
            if st.session_state.get("last_tools"):
                st.markdown("##### 🛠️ Chi tiết công cụ Machine Learning (Lượt cuối):")
                for t in st.session_state.last_tools:
                    st.markdown(f"- **Công cụ:** `{t.get('tool_name')}`")
                    render_tool_output({"Tham số đầu vào": t.get("arguments"), "Kết quả trả về": t.get("result")})

    # ==========================================================================
    # LUỒNG CUỘN TRANG (SCROLL DOWN FLOW): KHÁM PHÁ THÊM CÁC DẠNG BÊN DƯỚI
    # ==========================================================================
    st.markdown("<br><hr style='border-color: rgba(56, 189, 248, 0.2);'><br>", unsafe_allow_html=True)
    st.markdown("### 🧭 Khám Phá Thị Trường Bất Động Sản (Scroll Down Discovery)")
    st.caption("Cuộn xuống dưới để khám phá 3 phân khúc K-Means, bộ lọc giá đô thị và các đặc trưng chi phối định giá.")

    # 1. BỐN PHÂN KHÚC THỊ TRƯỜNG: ngưỡng giá, số liệu tính trực tiếp từ dữ liệu
    st.markdown("#### 🏛️ 4 Phân Khúc Thị Trường (Theo Ngưỡng Giá)")
    st.caption("Phân khúc xác định theo ngưỡng giá chung toàn quốc; K-Means (giá + diện tích) dùng để kiểm chứng cấu trúc thị trường.")
    seg_cols = st.columns(4)
    seg_colors = ["#38BDF8", "#60A5FA", "#A78BFA", "#F472B6"]

    for idx, (col, seg, color) in enumerate(zip(seg_cols, segment_table(), seg_colors), start=1):
        if seg["max"] == float("inf"):
            price_txt = f"&gt; {seg['min']:.1f} Tỷ VNĐ"
        elif seg["min"] == 0:
            price_txt = f"&lt; {seg['max']:.1f} Tỷ VNĐ"
        else:
            price_txt = f"{seg['min']:.1f} – {seg['max']:.1f} Tỷ VNĐ"
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="card-tag">Phân khúc 0{idx}</div>
                    <div class="card-val" style="color: {color};">{seg['name']}</div>
                    <div style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.5rem;">{price_txt}</div>
                    <div class="card-desc">
                        • <b>Quy mô:</b> {seg['share_pct']}% số tin ({seg['count']:,} căn)<br>
                        • <b>Diện tích đất TB:</b> ~{seg['mean_land_area']:.0f} m²<br>
                        • <b>Phổ biến:</b> {seg['median_bedrooms']} phòng ngủ, {seg['median_floors']} tầng<br>
                        • <b>Loại nhà nhiều nhất:</b> {seg['top_property_type']} ({seg['top_property_share_pct']:.0f}%)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. LĂNG KÍNH ĐÔ THỊ (URBAN LENS)
    st.markdown("#### 🏙️ Lăng Kính Đô Thị (Urban Market Lens)")
    df_clean = load_listing_data()
    all_provinces = sorted(df_clean["Province"].unique().tolist())

    c_select_col, c_stat_col = st.columns([1, 2])
    with c_select_col:
        selected_prov = st.selectbox(
            "Chọn tỉnh/thành phố cần soi kính hiển vi:",
            all_provinces,
            index=all_provinces.index("Hà Nội") if "Hà Nội" in all_provinces else 0,
        )
        c_stats = get_market_statistics(selected_prov)

    with c_stat_col:
        if c_stats.get("status") == "success":
            m_cols = st.columns(3)
            with m_cols[0]:
                st.metric("Tổng giao dịch", f"{c_stats.get('total_listings', 0):,} căn")
            with m_cols[1]:
                st.metric("Giá trung vị", c_stats.get("median_price_formatted", "N/A"))
            with m_cols[2]:
                st.metric("Đơn giá trung bình", c_stats.get("avg_price_per_m2", "N/A"))
            st.caption(
                f"Biên độ dao động giá tại **{selected_prov}**: {c_stats.get('min_price_formatted', 'N/A')} — {c_stats.get('max_price_formatted', 'N/A')}. "
                f"Diện tích đất trung bình: {c_stats.get('avg_land_area_m2', 0)} m²."
            )

    # 3. YẾU TỐ ĐẨY GIÁ NHÀ (FEATURE IMPORTANCE)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚖️ Yếu Tố Nào Quyết Định Giá Trị Căn Nhà? (Random Forest Insights)")
    _, _, _, _, _, feat_imp = get_trained_models()
    top_feats = feat_imp.head(6)

    # Nâng cấp lên Altair để tùy biến xoay chữ 45 độ và thêm số % trên đỉnh cột
    import altair as alt
    
    # Chuẩn bị dữ liệu và tạo thêm cột "Nhãn hiển thị" có chứa ký tự %
    bar_df = pd.DataFrame({
        "Đặc trưng": [FEATURE_LABELS.get(n, n) for n in top_feats.index],
        "Tỷ lệ tác động (%)": (top_feats.values * 100).round(1)
    })
    bar_df["Nhãn hiển thị"] = bar_df["Tỷ lệ tác động (%)"].astype(str) + "%"

    # Cấu hình trục đồ thị (Xoay chữ 45 độ, đổi màu chữ thành trắng ngà)
    base = alt.Chart(bar_df).encode(
        x=alt.X("Đặc trưng:N", 
                sort="-y", # Tự động sắp xếp cột cao nhất lên trước
                axis=alt.Axis(labelAngle=-45, labelColor="#E2E8F0", labelFontSize=16, title=None)),
        y=alt.Y("Tỷ lệ tác động (%):Q", 
                axis=alt.Axis(labelColor="#E2E8F0", titleColor="#E2E8F0", gridColor="rgba(255,255,255,0.1)", title="Mức độ ảnh hưởng (%)"))
    )

    # 1. Vẽ các cột màu xanh Neon bo góc mềm mại
    bars = base.mark_bar(color="#00F0FF", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)

    # 2. Vẽ các con số % hiển thị bay lơ lửng trên đỉnh cột
    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-6,  # Đẩy chữ lên trên 6px so với đỉnh cột
        color='#38BDF8', # Chữ xanh lơ sáng
        fontSize=13,
        fontWeight='bold'
    ).encode(
        text="Nhãn hiển thị:N"
    )

    # Gộp cột và chữ, ép nền trong suốt tuyệt đối
    chart = (bars + text).properties(height=380, background="transparent")
    
    # Xuất ra giao diện (Tham số theme=None cực kỳ quan trọng để vô hiệu hóa nền trắng mặc định)
    st.altair_chart(chart, width="stretch", theme=None)

    report = get_model_report()
    st.caption(
        f"Độ chính xác trên tập kiểm tra: R² = {report['r2_log']:.3f} (trên log giá), sai số trung bình khoảng {report['mape_pct']:.0f}%. "
        "Các cột one-hot (VD: Province_Hà Nội) đã được gộp về biến gốc."
    )

# ==============================================================================
# TAB 2: TOÀN CẢNH THỊ TRƯỜNG & KHÁM PHÁ DỮ LIỆU
# ==============================================================================
with explore_tab:
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">Toàn Cảnh Thị Trường Bất Động Sản</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Bản đồ số liệu trực quan trích xuất từ bộ dữ liệu giao dịch bất động sản toàn quốc...</div>', unsafe_allow_html=True)

    df_exp = load_listing_data()

    # Bảng 4 KPI vĩ mô
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Tổng Giao Dịch", f"{len(df_exp):,} căn")
    with kpi2:
        st.metric("Giá Trung Vị", f"{df_exp['Price_Billion_VND'].median():.2f} tỷ VNĐ")
    with kpi3:
        st.metric("Đơn Giá TB", f"{df_exp['price_per_m2'].mean():.1f} tr/m²")
    with kpi4:
        st.metric("Diện Tích TB", f"{df_exp['Land_Area'].mean():.0f} m²")

    st.markdown("<br>", unsafe_allow_html=True)

    # Top khu vực đắt đỏ nhất và giá tốt nhất
    top_c1, top_c2 = st.columns(2)
    with top_c1:
        st.markdown("##### 💎 Top 5 Khu Vực Đắt Đỏ Nhất (Theo Giá Trung Vị)")
        top_exp = df_exp.groupby("Province")["Price_Billion_VND"].median().sort_values(ascending=False).head(5)
        st.dataframe(pd.DataFrame({"Tỉnh/Thành phố": top_exp.index, "Giá trung vị": top_exp.map("{:.2f} tỷ VNĐ".format)}), width="stretch")

    with top_c2:
        st.markdown("##### 🏷️ Top 5 Khu Vực Giá Tốt Dễ Tiếp Cận Nhất")
        top_aff = df_exp.groupby("Province")["Price_Billion_VND"].median().sort_values(ascending=True).head(5)
        st.dataframe(pd.DataFrame({"Tỉnh/Thành phố": top_aff.index, "Giá trung vị": top_aff.map("{:.2f} tỷ VNĐ".format)}), width="stretch")

    # --------------------------------------------------------------------------
    # KHÁM PHÁ DỮ LIỆU CHUYÊN SÂU (EDA GALLERY - 9 BIỂU ĐỒ)
    # --------------------------------------------------------------------------
    st.markdown("<br><hr style='border-color: rgba(56, 189, 248, 0.2);'><br>", unsafe_allow_html=True)
    st.markdown("### 📈 Phòng Trưng Bày Trực Quan Hóa Dữ Liệu (EDA Gallery - 9 Biểu Đồ Chuyên Sâu)")
    st.caption("Các biểu đồ thống kê cốt lõi trích xuất từ quy trình làm sạch và phân tích khám phá dữ liệu bất động sản Việt Nam.")

    eda_dir = os.path.join(os.path.dirname(__file__), "vietnam_housing_data", "eda_charts")

    if os.path.exists(eda_dir):
        eda_tab1, eda_tab2, eda_tab3, eda_tab_zoom = st.tabs(
            [
                "🧹 1. Làm Sạch & Phân Phối Giá",
                "🏡 2. Diện Tích & Loại Hình BĐS",
                "🗺️ 3. Địa Lý & Ma Trận Tương Quan",
                "🔍 4. Kính Lúp Soi Biểu Đồ Bản To",
            ]
        )

        with eda_tab1:
            e1_col1, e1_col2, e1_col3 = st.columns(3)
            with e1_col1:
                img1_path = os.path.join(eda_dir, "01_missing_values.png")
                if os.path.exists(img1_path):
                    st.image(img1_path, caption="Biểu đồ 01: Tỷ Lệ Ô Khuyết (Dữ Liệu Gốc)", width="stretch")
                    st.caption("🔍 **Nhận xét**: Loại bỏ triệt để 100% các ô thiếu, bảo toàn 9,714 dòng sạch.")
            with e1_col2:
                img2_path = os.path.join(eda_dir, "02_price_histograms.png")
                if os.path.exists(img2_path):
                    st.image(img2_path, caption="Biểu đồ 02: Phân Phối Giá & Log Transform", width="stretch")
                    st.caption("🔍 **Nhận xét**: Giá lệch phải mạnh (độ lệch ≈ 4,3); sau log(1 + giá) còn ≈ 0,65, gần đối xứng hơn nhiều.")
            with e1_col3:
                img3_path = os.path.join(eda_dir, "03_correlation_with_log_price.png")
                if os.path.exists(img3_path):
                    st.image(img3_path, caption="Biểu đồ 03: Tương Quan Với Log Giá", width="stretch")
                    st.caption("🔍 **Nhận xét**: Diện tích đất và diện tích sàn là hai biến tương quan dương mạnh nhất.")

        with eda_tab2:
            e2_col1, e2_col2, e2_col3 = st.columns(3)
            with e2_col1:
                img4_path = os.path.join(eda_dir, "04_land_area_vs_price.png")
                if os.path.exists(img4_path):
                    st.image(img4_path, caption="Biểu đồ 04: Diện Tích Đất vs Giá Bán", width="stretch")
                    st.caption("🔍 **Nhận xét**: Giá tăng theo diện tích (thang log); cùng diện tích, khu vực trung tâm có giá cao hơn rõ rệt.")
            with e2_col2:
                img5_path = os.path.join(eda_dir, "05_price_by_property_type.png")
                if os.path.exists(img5_path):
                    st.image(img5_path, caption="Biểu đồ 05: Phân Phối Giá Theo Loại Hình", width="stretch")
                    st.caption("🔍 **Nhận xét**: Biệt thự có giá trung vị cao nhất (≈ 13,7 tỷ); nhà phố và chung cư chiếm phần lớn số tin.")
            with e2_col3:
                img6_path = os.path.join(eda_dir, "06_price_by_location_type.png")
                if os.path.exists(img6_path):
                    st.image(img6_path, caption="Biểu đồ 06: Phân Phối Giá Theo Vị Trí", width="stretch")
                    st.caption("🔍 **Nhận xét**: BĐS vùng trung tâm có đơn giá cao và độ phân hóa vượt trội.")

        with eda_tab3:
            e3_col1, e3_col2, e3_col3 = st.columns(3)
            with e3_col1:
                img7_path = os.path.join(eda_dir, "07_distance_vs_price_per_m2.png")
                if os.path.exists(img7_path):
                    st.image(img7_path, caption="Biểu đồ 07: Cự Ly Trung Tâm vs Đơn Giá/m²", width="stretch")
                    st.caption("🔍 **Nhận xét**: Định luật khoảng cách: Đơn giá giảm nhanh trong những km đầu rồi đi ngang từ khoảng 20 km trở ra.")
            with e3_col2:
                img8_path = os.path.join(eda_dir, "08_median_price_by_province.png")
                if os.path.exists(img8_path):
                    st.image(img8_path, caption="Biểu đồ 08: Giá Trung Vị Theo Tỉnh Thành", width="stretch")
                    st.caption("🔍 **Nhận xét**: TP.HCM, Hà Nội và Đà Nẵng định hình trục tam giác giá trị cao nhất.")
            with e3_col3:
                img9_path = os.path.join(eda_dir, "09_correlation_heatmap.png")
                if os.path.exists(img9_path):
                    st.image(img9_path, caption="Biểu đồ 09: Ma Trận Nhiệt Tương Quan Đa Biến", width="stretch")
                    st.caption("🔍 **Nhận xét**: Tương quan giữa 13 biến (12 biến số và log giá).")

        with eda_tab_zoom:
            chart_options = {
                "01_missing_values.png": "01. Phân Tích Ô Khuyết (Missing Values)",
                "02_price_histograms.png": "02. Phân Phối Giá & Chuẩn Hóa Log",
                "03_correlation_with_log_price.png": "03. Hệ Số Tương Quan Tuyến Tính Với Log Giá",
                "04_land_area_vs_price.png": "04. Tương Quan Phân Tán Diện Tích vs Giá Bán",
                "05_price_by_property_type.png": "05. Phân Phối Giá Theo Loại Hình Bất Động Sản",
                "06_price_by_location_type.png": "06. Phân Phối Giá Theo Vị Trí Đô Thị",
                "07_distance_vs_price_per_m2.png": "07. Khoảng Cách Đến Trung Tâm vs Đơn Giá/m²",
                "08_median_price_by_province.png": f"08. Giá Trung Vị Theo {df_exp['Province'].nunique()} Tỉnh/Thành",
                "09_correlation_heatmap.png": "09. Ma Trận Nhiệt Tương Quan Đa Biến (Heatmap)",
            }
            selected_chart_file = st.selectbox(
                "Chọn biểu đồ bạn muốn soi kính hiển vi bản to:",
                options=list(chart_options.keys()),
                format_func=lambda k: chart_options[k],
            )
            zoom_path = os.path.join(eda_dir, selected_chart_file)
            if os.path.exists(zoom_path):
                st.image(zoom_path, caption=chart_options[selected_chart_file], width="stretch")
    else:
        st.info("Chưa tìm thấy thư mục eda_charts. Hãy chạy 'python vietnam_housing_data/02_eda.py' để khởi tạo.")

# ==============================================================================
# TAB 3: CÀI ĐẶT HỆ THỐNG & KẾT NỐI LLM (ẨN KHỎI GIAO DIỆN CHÍNH)
# ==============================================================================
with settings_tab:
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">Cài Đặt Hệ Thống & Kết Nối AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Quản trị khóa API OpenRouter, lựa chọn mô hình ngôn ngữ và tùy chỉnh bộ điều phối Agent.</div>', unsafe_allow_html=True)

    set_c1, set_c2 = st.columns([1.5, 1])

    with set_c1:
        st.markdown("#### 🔑 Quản Trị Cổng LLM (Gemini / OpenRouter)")
        model_list = [
            "gemini-3.5-flash-lite",
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-chat",
            "mistralai/mistral-large-2411",
            "google/gemini-2.0-flash-001",
        ]
        chosen_m = st.selectbox(
            "Lựa chọn Model LLM:",
            options=model_list,
            index=model_list.index(st.session_state.selected_model) if st.session_state.selected_model in model_list else 0,
        )
        st.session_state.selected_model = chosen_m

        prov_id = get_provider(chosen_m)
        prov = PROVIDERS[prov_id]
        new_key = st.text_input(
            f"{prov['label']} API Key",
            value=st.session_state.api_keys.get(prov_id, ""),
            type="password",
            placeholder="AIza..." if prov_id == "gemini" else "sk-or-v1-...",
            help=f"Khóa này chỉ dùng cho các model chạy qua {prov['label']} (biến môi trường {prov['env']}).",
            key=f"api_key_input_{prov_id}",
        )
        if new_key != st.session_state.api_keys.get(prov_id, ""):
            st.session_state.api_keys[prov_id] = new_key
            st.success("Đã cập nhật API Key vào phiên làm việc hiện tại!")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🧹 Quản Trị Phiên Làm Việc (Session State)")
        if st.button("Làm Mới Lịch Sử Hội Thoại (Reset Chat)", width="stretch"):
            st.session_state.chat_history = []
            st.session_state.shoji_q = ""
            st.session_state.shoji_a = ""
            st.session_state.last_tools = []
            st.rerun()

    with set_c2:
        st.markdown("#### 📡 Trạng Thái Hệ Thống")
        if current_api_key():
            st.markdown(
                """
                <div class="feature-card" style="border-left: 4px solid #10B981;">
                    <div style="color: #10B981; font-weight: 700; margin-bottom: 0.3rem;">🟢 ONLINE - ĐÃ NHẬP API KEY</div>
                    <div class="card-desc">Sẵn sàng nhận diện Function Calling và sinh ngôn ngữ tự nhiên thông minh từ LLM.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="feature-card" style="border-left: 4px solid #F59E0B;">
                    <div style="color: #F59E0B; font-weight: 700; margin-bottom: 0.3rem;">🟡 CHẾ ĐỘ PHÂN TÍCH NỘI BỘ (OFFLINE)</div>
                    <div class="card-desc">Chưa nhập API Key. Hệ thống sử dụng bộ điều phối Heuristic nội bộ, vẫn gọi đầy đủ 6 công cụ Machine Learning mà không phát sinh lỗi.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="feature-card">
                <div class="card-tag">Đồ Án Jetking ADAI</div>
                <div style="color: #FFFFFF; font-weight: 600; margin-bottom: 0.3rem;">HouseAssist v2.0</div>
                <div class="card-desc">
                    • Mẫu thiết kế: SkyAssist Single-Model Pattern<br>
                    • Engine: Scikit-Learn + LLM API (Gemini / OpenRouter)<br>
                    • Học viên: Minh, Bách, Hoài
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Khối tùy biến Video Nền Cực Quang
    st.markdown("<br><hr style='border-color: rgba(56, 189, 248, 0.2);'><br>", unsafe_allow_html=True)
    st.markdown("#### 🎬 Tùy Biến Video Nền Cực Quang (Ambient Motion Canvas)")
    st.caption("Tùy chỉnh chuyển động cực quang mờ ảo dưới đáy giao diện theo sở thích thị giác hoặc cấu hình phần cứng.")

    bg_c1, bg_c2, bg_c3 = st.columns([1, 1.2, 1.2])
    with bg_c1:
        st.markdown("<br>", unsafe_allow_html=True)
        bg_toggle = st.toggle("Bật Video Nền", value=st.session_state.enable_video_bg, help="Bật hoặc tắt phông nền video cực quang động.")
        if bg_toggle != st.session_state.enable_video_bg:
            st.session_state.enable_video_bg = bg_toggle
            st.rerun()

    with bg_c2:
        new_blur = st.slider(
            "Độ mờ kính khuếch tán (Blur)",
            min_value=0,
            max_value=25,
            value=st.session_state.bg_blur,
            step=1,
            disabled=not st.session_state.enable_video_bg,
            help="Tăng độ mờ để ánh sáng dịu hơn; giảm độ mờ để nhìn rõ vệt sáng hơn."
        )
        if new_blur != st.session_state.bg_blur:
            st.session_state.bg_blur = new_blur
            st.rerun()

    with bg_c3:
        new_dark = st.slider(
            "Độ phủ tối tương phản (Dark Scrim %)",
            min_value=5,
            max_value=75,
            value=st.session_state.bg_darkness,
            step=5,
            disabled=not st.session_state.enable_video_bg,
            help="Tăng độ tối để chữ trắng và bảng biểu nổi bật hơn."
        )
        if new_dark != st.session_state.bg_darkness:
            st.session_state.bg_darkness = new_dark
            st.rerun()