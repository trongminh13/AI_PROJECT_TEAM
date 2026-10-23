"""
Module: scroll_view.py
Thành phần giao diện: 4 Cuộn Thư Gợi Ý Cổ Xưa (Ancient Oriental Scrolls)
Render kết hợp Streamlit Native Button Overlay để đạt chuẩn Zero-Reload WebSocket Interaction.
- Khi đóng: Hiển thị ống cuộn giấy buộc dây lụa đỏ ("Cuộn 1", "Cuộn 2", "Cuộn 3", "Cuộn 4").
- Khi hover: Giấy mở dãn ngang sang trái, lộ rõ tiêu đề câu hỏi gợi ý và dấu triện son.
- Khi click: Kích hoạt st.button native của Streamlit, hoàn toàn 0% reload/reset trang!
"""

SCROLL_ITEMS = [
    {
        "id": "1",
        "label": "Cuộn 1",
        "title": "📊 Thống kê Seattle",
        "subtitle": "Thị trường & giá trung vị",
        "seal": "市",
        "prompt": "Cho tôi biết thống kê thị trường nhà đất tại thành phố Seattle?"
    },
    {
        "id": "2",
        "label": "Cuộn 2",
        "title": "💰 Định giá Bellevue",
        "subtitle": "Nhà 2,200 sqft, 3PN, 2PT",
        "seal": "価",
        "prompt": "Dự đoán giá căn nhà 2,200 sqft, 3 phòng ngủ, 2 phòng tắm tại Bellevue?"
    },
    {
        "id": "3",
        "label": "Cuộn 3",
        "title": "🏯 Phân khúc 3 tầng",
        "subtitle": "Phân cụm tự nhiên K-Means",
        "seal": "層",
        "prompt": "Giải thích 3 phân khúc thị trường K-Means tại King County?"
    },
    {
        "id": "4",
        "label": "Cuộn 4",
        "title": "🌸 Tìm nhà Kent ~$500k",
        "subtitle": "Lọc nhà phù hợp ngân sách",
        "seal": "居",
        "prompt": "Tìm giúp tôi các căn nhà có giá khoảng 500,000 USD tại Kent?"
    }
]

def get_scroll_styles() -> str:
    """Trả về CSS toàn diện cho 4 cuộn thư cổ xưa và cơ chế overlay button native."""
    return """
<style>
  :root {
    --h: 86px;
    --open: 215px;
    --rod: 13px;
    --roll: 94px;
    --dur: 0.85s;
    --ease: cubic-bezier(.45, .05, .25, 1);
    --silk: #7b2d26;
  }

  .scroll-header-block {
    width: 100%;
    text-align: right;
    padding-right: 4px;
    border-bottom: 2px solid rgba(212, 178, 122, 0.35);
    padding-bottom: 6px;
    margin-bottom: 12px;
  }
  .scroll-header-block h3 {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #FFFFFF !important;
    letter-spacing: 0.3px;
    margin: 0 0 2px 0;
  }
  .scroll-header-block p {
    font-size: 0.82rem;
    color: rgba(233, 216, 180, 0.85) !important;
    margin: 0;
    font-style: italic;
  }

  /* Khung bao bọc từng cuộn thư ở cấp Streamlit layout wrapper */
  div[data-testid="stLayoutWrapper"]:has(.scroll-item-box) {
    margin-bottom: 18px !important;
    margin-top: 6px !important;
    height: auto !important;
  }

  /* Container cho mỗi cuộn thư kết hợp nút Streamlit overlay */
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box) {
    position: relative !important;
    min-height: 104px !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-end !important;
    justify-content: center !important;
  }

  /* Lớp cuộn thư hiển thị đồ họa: Nằm trong flow tự nhiên để giữ chiều cao chuẩn và chừa đệm cho mấu mạ vàng */
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box) div.element-container:has(.scroll-item-box) {
    position: relative !important;
    width: 100% !important;
    height: 86px !important;
    margin-top: 9px !important;
    margin-bottom: 9px !important;
    display: flex !important;
    justify-content: flex-end !important;
    z-index: 2 !important;
    pointer-events: none !important;
    padding: 0 !important;
  }

  /* Lớp nút Streamlit native trong suốt phủ lên trên để hứng sự kiện click */
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box) div.element-container:has(div.stButton) {
    position: absolute !important;
    right: 0 !important;
    top: 0 !important;
    width: 250px !important;
    height: 104px !important;
    z-index: 10 !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box) div.stButton {
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box) div.stButton > button {
    width: 100% !important;
    height: 104px !important;
    opacity: 0.0001 !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }

  /* ================= CHI TIẾT ĐỒ HỌA CUỘN THƯ ================= */
  .scroll-item-box {
    display: inline-flex;
    align-items: center;
    user-select: none;
    font-family: "Palatino Linotype", "Book Antiqua", Georgia, "Noto Serif", serif;
  }
  .scroll {
    display: inline-flex;
    align-items: center;
    outline: none;
    filter: drop-shadow(0 10px 12px rgba(0,0,0,.65));
    transition: transform 0.25s ease;
  }

  /* Trục gỗ mun mạ vàng */
  .rod {
    position: relative;
    flex: none;
    width: var(--rod);
    height: var(--h);
    background: linear-gradient(90deg, #2a1608, #633c1d 30%, #9e6435 50%, #633c1d 70%, #2a1608);
    border-radius: 1px;
    z-index: 10;
  }
  .rod::before, .rod::after {
    content: "";
    position: absolute;
    left: -2px;
    right: -2px;
    height: 10px;
    background: linear-gradient(90deg, #d4af37, #fff0a8 45%, #d4af37 70%, #7a5813);
    border-radius: 2px;
    box-shadow: 0 1px 2px rgba(0,0,0,.5);
    z-index: 12;
  }
  .rod::before { top: -7px; }
  .rod::after  { bottom: -7px; }

  .left-rod {
    z-index: 15;
    box-shadow: -2px 0 6px rgba(0,0,0,.4);
  }

  /* Tờ giấy mở rộng sang trái */
  .paper {
    position: relative;
    width: 0;
    height: var(--h);
    overflow: hidden;
    background:
      linear-gradient(180deg,
        rgba(123, 45, 38, .92) 0 7px,
        transparent 7px calc(100% - 7px),
        rgba(123, 45, 38, .92) calc(100% - 7px) 100%
      ),
      linear-gradient(90deg,
        rgba(0,0,0,.22) 0,
        transparent 14px,
        transparent calc(100% - 14px),
        rgba(0,0,0,.35) 100%
      ),
      radial-gradient(ellipse at 50% 50%, #f6eccb 0%, #ecd9a7 60%, #dfc386 100%);
    box-shadow:
      inset 0 0 16px rgba(110, 70, 25, .25),
      0 4px 10px rgba(0,0,0,.45);
    transition: width var(--dur) var(--ease);
    display: flex;
    align-items: center;
  }
  .paper::before, .paper::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 7px;
    background:
      repeating-linear-gradient(90deg,
        #b14336 0 5px,
        #7b2d26 5px 10px,
        #d4b27a 10px 12px
      );
    z-index: 3;
    box-shadow: 0 0 2px rgba(0,0,0,.3);
  }
  .paper::before { top: 0; }
  .paper::after  { bottom: 0; }

  /* Nội dung bên trong tờ giấy */
  .paper-content {
    position: absolute;
    right: 0;
    width: var(--open);
    height: 100%;
    box-sizing: border-box;
    padding: 10px 12px 10px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    white-space: nowrap;
    opacity: 0;
    transform: translateX(18px);
    transition: opacity .4s ease .3s, transform .4s var(--ease) .3s;
  }

  .text-block {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 3px;
    overflow: hidden;
  }
  .main-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 0.96rem;
    font-weight: 700;
    color: #4a2408;
    text-shadow: 0 1px 0 rgba(255,255,255,.4);
    letter-spacing: .2px;
  }
  .sub-title {
    font-size: 0.72rem;
    color: #7b4e28;
    letter-spacing: .1px;
    font-style: italic;
  }

  /* Con dấu triện son */
  .seal {
    flex: none;
    width: 28px;
    height: 28px;
    border: 2px solid #a32015;
    border-radius: 4px;
    color: #a32015;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
    font-weight: 900;
    font-size: 15px;
    line-height: 1;
    background: rgba(163, 32, 21, .08);
    box-shadow:
      inset 0 0 3px rgba(163, 32, 21, .3),
      0 0 1px rgba(163, 32, 21, .5);
    margin-left: 6px;
  }

  /* Cuộn dày bên phải */
  .bundle {
    position: relative;
    width: var(--roll);
    height: var(--h);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: width var(--dur) var(--ease);
    z-index: 5;
  }
  .right-rod {
    position: absolute;
    right: 0;
    top: 0;
    z-index: 10;
  }

  .roll-paper {
    position: absolute;
    left: 0;
    right: var(--rod);
    top: 3px;
    bottom: 3px;
    background:
      repeating-linear-gradient(90deg,
        #b88a44 0 2px,
        #875b24 2px 4px,
        #d8b067 4px 7px,
        #9d6f2c 7px 9px
      );
    border-radius: 4px 0 0 4px;
    box-shadow:
      inset 2px 0 5px rgba(0,0,0,.5),
      inset 0 3px 4px rgba(0,0,0,.35),
      inset 0 -3px 4px rgba(0,0,0,.35),
      -3px 0 8px rgba(0,0,0,.45);
    transition: opacity .3s ease;
  }
  .roll-paper::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 9px;
    background:
      linear-gradient(180deg,
        #7b2d26 0 6px,
        transparent 6px calc(100% - 6px),
        #7b2d26 calc(100% - 6px) 100%
      ),
      #e8d39e;
    border-radius: 4px 0 0 4px;
    box-shadow: inset 1px 0 2px rgba(0,0,0,.3);
  }

  /* Nhãn tên Cuộn 1, Cuộn 2... */
  .roll-label {
    position: absolute;
    left: calc(50% - 6px);
    top: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 0.85rem;
    font-weight: 800;
    color: #3b1d06;
    letter-spacing: 0.5px;
    z-index: 25;
    background: rgba(245, 230, 195, 0.92);
    padding: 3px 10px;
    border-radius: 4px;
    border: 1px solid #7a4b22;
    box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    pointer-events: none;
    transition: opacity 0.3s ease, transform 0.3s ease;
    white-space: nowrap;
  }

  /* Dải lụa đỏ buộc nơ */
  .tie {
    position: absolute;
    left: calc(50% - 6px);
    top: 0;
    bottom: 0;
    width: 13px;
    transform: translateX(-50%);
    background:
      linear-gradient(90deg,
        #61140e 0,
        #a52219 25%,
        #e34d40 50%,
        #a52219 75%,
        #61140e 100%
      );
    box-shadow:
      0 0 4px rgba(0,0,0,.6),
      inset 0 1px 0 rgba(255,255,255,.2);
    z-index: 8;
    transition: transform .5s var(--ease), opacity .35s ease;
  }
  .tie::before {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    width: 17px;
    height: 12px;
    transform: translate(-50%, -50%);
    background: radial-gradient(circle at 40% 40%, #e34d40, #801911 75%);
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,.5);
  }
  .tie::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 54%;
    width: 8px;
    height: 24px;
    transform: translateX(-50%);
    background: linear-gradient(90deg, #8e1d16, #d03a2f, #8e1d16);
    border-radius: 0 0 3px 3px;
    box-shadow: -8px 4px 0 -1px #a52219;
  }

  /* ================= HOVER TRIGGER KHI RÊ CHUỘT VÀO CONTAINER ================= */
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .scroll {
    transform: translateY(-2px);
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .paper {
    width: var(--open) !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .bundle {
    width: var(--rod) !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .roll-paper {
    opacity: 0 !important;
    transition: opacity .4s ease 0.55s !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .roll-label {
    opacity: 0 !important;
    transform: translate(-50%, -50%) scale(0.6) !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .tie {
    transform: translateY(18px) rotate(6deg) !important;
    opacity: 0 !important;
  }
  div[data-testid="stVerticalBlock"]:has(> div.element-container .scroll-item-box):hover .paper-content {
    opacity: 1 !important;
    transform: translateX(0) !important;
  }
</style>
"""

def get_single_scroll_html(item: dict) -> str:
    """Sinh HTML cho 1 cuộn thư đơn lẻ, không có href hay JS inline để tránh lỗi React/Navigation."""
    return (
        f'<div class="scroll-item-box">\n'
        f'<div class="scroll" tabindex="0" title="Bấm để mở lời giải đáp trong Trà Thất">\n'
        f'<div class="rod left-rod"></div>\n'
        f'<div class="paper">\n'
        f'<div class="paper-content">\n'
        f'<div class="text-block">\n'
        f'<div class="main-title">{item["title"]}</div>\n'
        f'<div class="sub-title">{item["subtitle"]}</div>\n'
        f'</div>\n'
        f'<div class="seal">{item["seal"]}</div>\n'
        f'</div>\n'
        f'</div>\n'
        f'<div class="bundle">\n'
        f'<div class="rod right-rod"></div>\n'
        f'<div class="roll-paper"></div>\n'
        f'<span class="roll-label">{item["label"]}</span>\n'
        f'<div class="tie"></div>\n'
        f'</div>\n'
        f'</div>\n'
        f'</div>'
    )
