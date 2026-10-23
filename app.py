"""
Ứng dụng: app.py
Giao diện Web Streamlit cho HouseAssist - AI Real Estate Advisor & Analytics Agent
Thiết kế theo chuẩn mực Cao cấp, Thơ mộng & Sang trọng (Poetic Atmospheric Luxury):
- Nút bấm góc vuông sắc sảo (border-radius: 0px), phóng to nhẹ khi hover kèm viền xanh lam chuyển động loop neon.
- Cấu hình LLM & API được tách biệt gọn gàng vào Tab Cài Đặt (Settings).
- Luồng cuộn trang dọc (Vertical Scroll Flow): Khám phá thị trường 3 phân khúc K-Means, Lăng kính đô thị và Biểu đồ định giá.
"""

import os
import base64
import html
import json
import streamlit as st
import pandas as pd
import numpy as np
from agent import run_agent_turn, DEFAULT_MODEL
from data import load_clean_data, get_trained_models
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
    st.session_state.bg_blur = 2
if "bg_darkness" not in st.session_state:
    st.session_state.bg_darkness = 25

@st.cache_data
def get_ambient_video_b64(video_path: str = "assets/ambient_bg.mp4") -> str:
    """Nạp video và cache chuỗi base64 trong bộ nhớ RAM, tránh đọc lại đĩa khi tương tác."""
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


@st.cache_data
def get_output_font_b64(font_path: str = os.path.join(os.path.dirname(__file__), "SVN-Hottroof-Semhesta.otf")) -> str:
    """Đọc font output và cache để nhúng trực tiếp vào component trình duyệt."""
    if os.path.exists(font_path):
        with open(font_path, "rb") as font_file:
            return base64.b64encode(font_file.read()).decode("ascii")
    return ""


def render_tool_output(data: dict) -> None:
    """Hiển thị dữ liệu tool trong khung cuộn dùng font SVN Hottroof Semhesta."""
    font_b64 = get_output_font_b64()
    font_face = (
        f"@font-face{{font-family:'SVNHottroof';src:url(data:font/otf;base64,{font_b64}) format('opentype');font-display:swap}}"
        if font_b64
        else ""
    )
    formatted_json = html.escape(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    component_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
{font_face}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: transparent; color: #E2E8F0; }}
.output {{ height: 310px; overflow: auto; padding: 14px 16px; border: 1px solid rgba(183,157,114,.35); border-radius: 8px; background: rgba(7,11,25,.78); }}
pre {{ margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font-family: 'SVNHottroof', sans-serif; font-size: 15px; line-height: 1.65; }}
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
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">

    <style>
    /* Reset & Typography */
    html, body, [class*="css"] {{
        font-family: 'Outfit', sans-serif;
        color: #E2E8F0;
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
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF 20%, #A5F3FC 60%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
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
       - Chiều rộng bằng 2/3 so với lúc đầu (width: 67%), căn giữa cân đối
       - Đổi màu sang màu nâu giống khung gỗ Trà Thất Shoji (--wood-dark, --wood)
       - Khung hình chữ nhật bên trong bo góc mềm mại (border-radius: 16px)
       - Đặt sát ngay dưới khung Trà Thất
       ========================================================================== */
    [data-testid="stBottom"] > div {{
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        background: transparent !important;
    }}

    [data-testid="stBottom"] {{
        background: transparent !important;
        padding-bottom: 0.5rem !important;
    }}

    /* Triệt tiêu hoàn toàn khoảng hở đáy của iframe */
    div[data-testid="stIFrame"],
    .stIFrame,
    iframe[data-testid="stIFrame"] {{
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
        display: block !important;
    }}

    [data-testid="stChatInput"] {{
        width: 67% !important;
        max-width: 960px !important;
        margin: -16px auto 0.8rem auto !important;
        padding-bottom: 0.3rem !important;
    }}

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

# Cấu hình API key mặc định
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")
    try:
        if not st.session_state.api_key and "OPENROUTER_API_KEY" in st.secrets:
            st.session_state.api_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass

if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

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
            King County Real Estate AI
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Trạng thái kết nối LLM
    if st.session_state.api_key:
        st.markdown(
            """
            <div style="padding: 6px 12px; background: rgba(16, 185, 129, 0.15); border-left: 3px solid #10B981; margin-bottom: 1rem;">
                <span style="color: #10B981; font-weight: 600; font-size: 0.85rem;">🟢 Online (OpenRouter)</span><br>
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
        st.session_state.shoji_q = ""
        st.session_state.shoji_a = ""
        st.session_state.last_tools = []
        st.rerun()

    st.markdown("---")

    # Bảng chỉ số thị trường nhanh
    st.markdown("### 📊 Chỉ Số Thị Trường")
    try:
        df_side = load_clean_data()
        sb_c1, sb_c2 = st.columns(2)
        with sb_c1:
            st.metric("Giao dịch", f"{len(df_side):,}")
            st.metric("Đơn giá TB", f"${df_side['price_per_sqft'].mean():.0f}/sqft")
        with sb_c2:
            st.metric("Giá trung vị", f"${df_side['price'].median():,.0f}")
            st.metric("Diện tích TB", f"{df_side['sqft_living'].mean():.0f} sqft")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💎 **Top 3 khu vực đắt nhất:**")
        top3 = df_side.groupby("city")["price"].median().sort_values(ascending=False).head(3)
        for city_name, val in top3.items():
            st.markdown(f"- **{city_name}:** `${val:,.0f}`")
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
        '<div class="hero-subtitle">Hệ thống Trí tuệ Nhân tạo Phân tích, Định giá & Khám phá Bất động sản King County qua Không gian Thiền Định Shoji.</div>',
        unsafe_allow_html=True,
    )

    # BỐ CỤC 2 CỘT: KHUNG TRÀ THẤT TO RỘNG (BÊN TRÁI) - CỤM CUỘN THƯ CỔ XƯA SÁT BÊN PHẢI
    shoji_col, quick_col = st.columns([4.1, 1.35], gap="medium")
    quick_prompt = None

    # Bắt tín hiệu click cuộn thư từ query parameters
    if "quick_prompt" in st.query_params:
        quick_prompt = st.query_params["quick_prompt"]
        try:
            del st.query_params["quick_prompt"]
        except Exception:
            pass

    with shoji_col:
        # SÂN KHẤU TRÀ THẤT SHOJI DUY NHẤT (Single Master Sanctuary Theater)
        shoji_markup = get_shoji_html(st.session_state.shoji_q, st.session_state.shoji_a)
        st.iframe(src=shoji_markup, height=590, width="stretch")

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

    # Khung nhập liệu Chat Input gỗ ấm Shoji, bề ngang 2/3, đặt sát ngay dưới Khung Trà Thất
    chat_box = st.container()
    with chat_box:
        user_input = st.chat_input("✨ Đặt câu hỏi cho Trà Thất Shoji về định giá, phân khúc, vị trí hoặc tìm nhà...")
    active_prompt = quick_prompt or user_input

    if active_prompt:
        with st.spinner("Người trong Trà Thất Shoji đang mở sổ sách & kích hoạt mô hình AI..."):
            agent_history = [{"role": "user", "content": active_prompt}]
            response_text, tools_executed = run_agent_turn(
                messages=agent_history,
                api_key=st.session_state.api_key,
                model=st.session_state.selected_model,
            )
            # Cập nhật trực tiếp vào Khung Trà Thất Shoji duy nhất và rerun
            st.session_state.shoji_q = active_prompt
            st.session_state.shoji_a = response_text
            st.session_state.last_tools = tools_executed
            st.rerun()

    # Expander xem bản chép văn bản & chi tiết công cụ ML (nếu đã có câu trả lời)
    if st.session_state.get("shoji_a"):
        with st.expander("📜 Xem Bản Chép Văn Bản & Phân Tích Công Cụ (Transcript & Tool Inspection)", expanded=False):
            st.markdown(f"**Câu hỏi đã đặt:** {st.session_state.shoji_q}")
            st.markdown("---")
            st.markdown(st.session_state.shoji_a)
            if st.session_state.get("last_tools"):
                st.markdown("---")
                st.markdown("##### 🛠️ Chi tiết công cụ Machine Learning đã thực thi:")
                for t in st.session_state.last_tools:
                    st.markdown(f"- **Công cụ:** `{t.get('tool_name')}`")
                    render_tool_output({"Tham số đầu vào": t.get("arguments"), "Kết quả trả về": t.get("result")})

    # ==========================================================================
    # LUỒNG CUỘN TRANG (SCROLL DOWN FLOW): KHÁM PHÁ THÊM CÁC DẠNG BÊN DƯỚI
    # ==========================================================================
    st.markdown("<br><hr style='border-color: rgba(56, 189, 248, 0.2);'><br>", unsafe_allow_html=True)
    st.markdown("### 🧭 Khám Phá Thị Trường Bất Động Sản (Scroll Down Discovery)")
    st.caption("Cuộn xuống dưới để khám phá 3 phân khúc K-Means, bộ lọc giá đô thị và các đặc trưng chi phối định giá.")

    # 1. BA PHÂN KHÚC K-MEANS CHUYÊN SÂU
    st.markdown("#### 🏛️ 3 Phân Khúc Thị Trường Tự Nhiên (K-Means Clustering)")
    seg_cols = st.columns(3)

    with seg_cols[0]:
        st.markdown(
            """
            <div class="feature-card">
                <div class="card-tag">Phân khúc 01</div>
                <div class="card-val" style="color: #38BDF8;">Bình Dân</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.5rem;">~$330,000 USD</div>
                <div class="card-desc">
                    • <b>Diện tích TB:</b> ~1,430 sqft (133 m²)<br>
                    • <b>Quy mô:</b> 3 phòng ngủ, 1.5 phòng tắm<br>
                    • <b>Đặc điểm:</b> Nhà ở vừa túi tiền, phù hợp gia đình trẻ, tập trung tại Kent, Auburn, Federal Way.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with seg_cols[1]:
        st.markdown(
            """
            <div class="feature-card">
                <div class="card-tag">Phân khúc 02</div>
                <div class="card-val" style="color: #60A5FA;">Trung Cấp</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.5rem;">~$585,000 USD</div>
                <div class="card-desc">
                    • <b>Diện tích TB:</b> ~2,380 sqft (221 m²)<br>
                    • <b>Quy mô:</b> 3.6 phòng ngủ, 2.4 phòng tắm<br>
                    • <b>Đặc điểm:</b> Phân khúc phổ biến nhất (chiếm 41%), nhà ngoại ô hiện đại ở Renton, Kirkland, Bothell.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with seg_cols[2]:
        st.markdown(
            """
            <div class="feature-card">
                <div class="card-tag">Phân khúc 03</div>
                <div class="card-val" style="color: #C084FC;">Cao Cấp</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 0.5rem;">~$1,164,000 USD</div>
                <div class="card-desc">
                    • <b>Diện tích TB:</b> ~3,780 sqft (351 m²)<br>
                    • <b>Quy mô:</b> 4-5 phòng ngủ, 3.5 phòng tắm<br>
                    • <b>Đặc điểm:</b> Biệt thự ven hồ (waterfront), view vịnh tuyệt đẹp tại Seattle, Bellevue, Medina, Mercer Island.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. LĂNG KÍNH ĐÔ THỊ (URBAN LENS)
    st.markdown("#### 🏙️ Lăng Kính Đô Thị (Urban Market Lens)")
    df_clean = load_clean_data()
    all_cities = sorted(df_clean["city"].unique().tolist())

    c_select_col, c_stat_col = st.columns([1, 2])
    with c_select_col:
        selected_city = st.selectbox("Chọn thành phố cần soi kính hiển vi:", all_cities, index=all_cities.index("Seattle") if "Seattle" in all_cities else 0)
        c_stats = get_market_statistics(selected_city)

    with c_stat_col:
        if c_stats.get("status") == "success":
            m_cols = st.columns(3)
            with m_cols[0]:
                st.metric("Tổng giao dịch", f"{c_stats['total_transactions']:,} căn")
            with m_cols[1]:
                st.metric("Giá trung vị", c_stats["median_price_formatted"])
            with m_cols[2]:
                st.metric("Đơn giá trung bình", c_stats["avg_price_per_sqft"])
            st.caption(f"Biên độ dao động giá tại **{selected_city}**: {c_stats['min_price_formatted']} — {c_stats['max_price_formatted']}. Diện tích trung bình: {c_stats['avg_sqft_living']} sqft.")

    # 3. YẾU TỐ ĐẨY GIÁ NHÀ (FEATURE IMPORTANCE)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚖️ Yếu Tố Nào Quyết Định Giá Trị Căn Nhà? (Random Forest Insights)")
    _, _, _, _, _, feat_imp = get_trained_models()
    top_feats = feat_imp.head(6)

    bar_df = pd.DataFrame({"Đặc trưng": top_feats.index, "Tỷ lệ tác động (%)": (top_feats.values * 100).round(1)})
    st.bar_chart(bar_df.set_index("Đặc trưng"), color="#00F0FF")

# ==============================================================================
# TAB 3: TOÀN CẢNH THỊ TRƯỜNG & KHÁM PHÁ DỮ LIỆU
# ==============================================================================
with explore_tab:
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">Toàn Cảnh Thị Trường Bất Động Sản</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Bản đồ số liệu trực quan trích xuất từ 4,548 giao dịch sạch của King County, Washington.</div>', unsafe_allow_html=True)

    df_exp = load_clean_data()

    # Bảng 4 KPI vĩ mô
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Tổng Giao Dịch", f"{len(df_exp):,} căn")
    with kpi2:
        st.metric("Giá Trung Vị", f"${df_exp['price'].median():,.0f} USD")
    with kpi3:
        st.metric("Đơn Giá TB", f"${df_exp['price_per_sqft'].mean():.0f}/sqft")
    with kpi4:
        st.metric("Diện Tích TB", f"{df_exp['sqft_living'].mean():.0f} sqft")

    st.markdown("<br>", unsafe_allow_html=True)

    # Top khu vực đắt đỏ nhất và giá tốt nhất
    top_c1, top_c2 = st.columns(2)
    with top_c1:
        st.markdown("##### 💎 Top 5 Khu Vực Đắt Đỏ Nhất (Theo Giá Trung Vị)")
        top_exp = df_exp.groupby("city")["price"].median().sort_values(ascending=False).head(5)
        st.dataframe(pd.DataFrame({"Thành phố": top_exp.index, "Giá trung vị (USD)": top_exp.map("${:,.0f}".format)}), width="stretch")

    with top_c2:
        st.markdown("##### 🏷️ Top 5 Khu Vực Giá Tốt Dễ Tiếp Cận Nhất")
        top_aff = df_exp.groupby("city")["price"].median().sort_values(ascending=True).head(5)
        st.dataframe(pd.DataFrame({"Thành phố": top_aff.index, "Giá trung vị (USD)": top_aff.map("${:,.0f}".format)}), width="stretch")

# ==============================================================================
# TAB 4: CÀI ĐẶT HỆ THỐNG & KẾT NỐI LLM (ẨN KHỎI GIAO DIỆN CHÍNH)
# ==============================================================================
with settings_tab:
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">Cài Đặt Hệ Thống & Kết Nối AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Quản trị khóa API OpenRouter, lựa chọn mô hình ngôn ngữ và tùy chỉnh bộ điều phối Agent.</div>', unsafe_allow_html=True)

    set_c1, set_c2 = st.columns([1.5, 1])

    with set_c1:
        st.markdown("#### 🔑 Quản Trị Cổng LLM Gateway (OpenRouter)")
        new_key = st.text_input(
            "OpenRouter API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-or-v1-...",
            help="Lấy khóa API miễn phí từ https://openrouter.ai/keys để sử dụng các mô hình LLM.",
        )
        if new_key != st.session_state.api_key:
            st.session_state.api_key = new_key
            st.success("Đã cập nhật API Key vào phiên làm việc hiện tại!")

        model_list = [
            "openrouter/free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-r1:free",
            "mistralai/mistral-7b-instruct:free",
        ]
        chosen_m = st.selectbox(
            "Lựa chọn Model LLM:",
            options=model_list,
            index=model_list.index(st.session_state.selected_model) if st.session_state.selected_model in model_list else 0,
        )
        st.session_state.selected_model = chosen_m

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🧹 Quản Trị Phiên Làm Việc (Session State)")
        if st.button("Làm Mới Lịch Sử Hội Thoại (Reset Chat)", width="stretch"):
            st.session_state.shoji_q = ""
            st.session_state.shoji_a = ""
            st.session_state.last_tools = []
            st.rerun()

    with set_c2:
        st.markdown("#### 📡 Trạng Thái Hệ Thống")
        if st.session_state.api_key:
            st.markdown(
                """
                <div class="feature-card" style="border-left: 4px solid #10B981;">
                    <div style="color: #10B981; font-weight: 700; margin-bottom: 0.3rem;">🟢 ONLINE - KẾT NỐI OPENROUTER</div>
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
                    <div class="card-desc">Chưa nhập API Key. Hệ thống sử dụng bộ điều phối Heuristic nội bộ, vẫn gọi đầy đủ 5 công cụ Machine Learning mà không phát sinh lỗi.</div>
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
                    • Engine: Scikit-Learn + OpenRouter API<br>
                    • Học viên: Đỗ Trọng Minh
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
