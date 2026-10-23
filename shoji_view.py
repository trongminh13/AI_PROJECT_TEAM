"""
Module: shoji_view.py
Chế độ hiển thị: Không gian Thiền Định Shoji (Zen Real Estate Sanctuary)
Chuyển hóa từ shoji-chatbot.html sang component tương tác cho HouseAssist.
Kết nối trực tiếp kết quả phân tích học máy và LLM vào hoạt ảnh cửa trượt Shoji.
"""

import json

def get_shoji_html(question: str = "", answer: str = "") -> str:
    """
    Sinh mã HTML/CSS/JS khép kín cho Trà Thất Shoji.
    Nếu có answer: Tự động chạy hoạt ảnh mở cửa và hiện chữ thư pháp loang mờ.
    Nếu chưa có: Hiển thị cửa đóng với ánh đèn vàng ấm và bóng người mờ ảo bên trong.
    """
    safe_q = json.dumps(question, ensure_ascii=False)
    safe_a = json.dumps(answer, ensure_ascii=False)
    has_answer = "true" if (answer and answer.strip()) else "false"

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trà Thất Shoji - HouseAssist</title>
<style>
  :root {{
    --wood: #5a3d24;
    --wood-dark: #3a2616;
    --ink: #2b1d14;
    --paper: #f6edd8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 0px;
    background: transparent;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    color: #e7ddcc;
    overflow: hidden;
  }}
  .wrap {{ width: 100%; max-width: 100%; display: flex; flex-direction: column; gap: 0px; margin: 0 auto; }}

  /* ================= KHUNG CỬA ================= */
  .frame {{
    --pw: 17.4;                       /* chiều rộng người (% khung) */
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    overflow: hidden;
    border: 12px solid var(--wood-dark);
    border-radius: 6px;
    box-shadow: 0 20px 50px rgba(0,0,0,.7), inset 0 0 40px rgba(0,0,0,.5);
    background: #000;
  }}

  /* ---------- Căn phòng phía sau cửa ---------- */
  .room {{
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 30% 40%, #fff6dc 0%, #f4dfae 60%, #e4c98c 100%);
  }}
  .floor {{
    position: absolute; left: 0; right: 0; bottom: 0; height: 10%;
    background: repeating-linear-gradient(90deg, #c9b07a 0 118px, #b99f68 118px 120px);
    box-shadow: inset 0 6px 10px rgba(0,0,0,.18);
  }}
  .text {{
    position: absolute; left: 0; top: 0; bottom: 10%;
    width: 50%;
    padding: 5% 5% 4% 6%;
    overflow-y: auto;
    color: var(--ink);
    font-family: "Noto Serif JP", "Yu Mincho", "Hiragino Mincho ProN", Georgia, serif;
    font-size: clamp(13px, 1.6vw, 17px);
    line-height: 1.75;
    transition: opacity .5s;
    scrollbar-width: thin;
    scrollbar-color: #b99f68 transparent;
  }}
  .text.fade {{ opacity: 0; }}
  .text .q {{ font-size: .82em; color: #8a6a3e; margin-bottom: .8em; letter-spacing: .04em; font-weight: 700; }}
  .text p {{ margin-bottom: .85em; }}
  .w {{
    display: inline-block;
    opacity: 0;
    filter: blur(5px);
    transform: translateY(5px);
    transition: opacity .7s ease, filter .7s ease, transform .7s ease;
  }}
  .w.on {{ opacity: 1; filter: none; transform: none; }}
  .think {{ color: #8a6a3e; letter-spacing: .3em; animation: pulse 1.4s infinite; font-size: 1.5rem; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .25 }} 50% {{ opacity: 1 }} }}

  /* ---------- Hai cánh cửa Shoji ---------- */
  .door {{
    position: absolute; top: 0; bottom: 0; width: 50%;
    border: 6px solid var(--wood);
    background:
      repeating-linear-gradient(0deg, rgba(120,90,50,.035) 0 1px, transparent 1px 3px),
      radial-gradient(ellipse at 50% 40%, #fffaf0 0%, #f6edd8 65%, #e8dbb9 100%);
    will-change: transform;
  }}
  .door.left  {{ left: 0;   z-index: 5; }}
  .door.right {{ left: 50%; z-index: 6; }}
  .lattice {{
    position: absolute; left: 0; right: 0; top: 0; bottom: 12%;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(6, 1fr);
  }}
  .cell {{ border-right: 4px solid var(--wood); border-bottom: 4px solid var(--wood); }}
  .cell:nth-child(3n) {{ border-right: 0; }}
  .kick {{
    position: absolute; left: 0; right: 0; bottom: 0; height: 12%;
    background: linear-gradient(180deg, #6b4a2b, #4a321d);
    border-top: 5px solid var(--wood);
  }}
  .handle {{
    position: absolute; right: 3.5%; top: 48%;
    width: 22px; height: 22px; border-radius: 50%;
    background: radial-gradient(circle, #1b130d 38%, #8b6a45 42%, #d4b27a 100%);
    box-shadow: 0 1px 3px rgba(0,0,0,.4);
  }}
  .jamb {{
    position: absolute; left: 0; top: 0; bottom: 0; width: 8px;
    background: var(--wood-dark); z-index: 7;
  }}

  /* ================= NGƯỜI BÊN TRONG ================= */
  .person {{
    position: absolute;
    bottom: 6%;
    left: 80%;
    width: calc(var(--pw) * 1%);
    aspect-ratio: 1 / 2;
    transform: translateX(-50%);
    z-index: 8;
    pointer-events: none;
    opacity: 0;
    filter: blur(3.5px);
    transition: left 0s, opacity .5s, filter .4s;
  }}
  .person.shadow {{ opacity: .65; filter: blur(3.5px); }}
  .person.clear  {{ opacity: 1;  filter: none; }}
  .person svg {{ width: 100%; height: 100%; overflow: visible; display: block; }}
  .person svg * {{ fill: #140d08; }}
  .person svg .obi {{ fill: #2f2016; }}
  .person svg .armline {{ fill: none; stroke: #140d08; stroke-width: 9; stroke-linecap: round; }}

  .flip {{ transform-origin: 50px 0; }}
  .person.face-right .flip {{ transform: scaleX(-1); }}

  .arm {{ transform-origin: 44px 58px; transform: rotate(-90deg); transition: transform .6s ease; }}
  .person.reach .arm {{ transform: rotate(0deg); }}

  .person.walking .bodyg {{ animation: bob .22s infinite alternate ease-in-out; }}
  .person.walking .foot-a {{ animation: step .45s infinite alternate ease-in-out; }}
  .person.walking .foot-b {{ animation: step .45s infinite alternate-reverse ease-in-out; }}
  .person.walking:not(.reach) .arm {{ animation: armswing .45s infinite alternate ease-in-out; }}
  @keyframes bob {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-3px); }} }}
  @keyframes step {{ from {{ transform: translateX(-8px); }} to {{ transform: translateX(8px); }} }}
  @keyframes armswing {{ from {{ transform: rotate(-102deg); }} to {{ transform: rotate(-78deg); }} }}



  @media (max-width: 700px) {{
    .frame {{ aspect-ratio: 3 / 4; --pw: 26; }}
    .text {{ font-size: 13.5px; width: 100%; }}
  }}
</style>
</head>
<body>
<main class="wrap">

  <div class="frame" id="frame">
    <!-- Phòng phía sau -->
    <div class="room">
      <div class="floor"></div>
      <div class="text" id="text"></div>
    </div>

    <!-- Hai cánh cửa Shoji -->
    <div class="door left" id="doorL">
      <div class="lattice"></div><div class="kick"></div><div class="handle"></div>
    </div>
    <div class="door right" id="doorR">
      <div class="lattice"></div><div class="kick"></div>
    </div>
    <div class="jamb"></div>

    <!-- Người trong phòng -->
    <div class="person face-left" id="person">
      <svg viewBox="0 0 100 200" aria-hidden="true">
        <g class="flip">
          <g class="foot foot-a"><ellipse cx="42" cy="188" rx="10" ry="5"/></g>
          <g class="foot foot-b"><ellipse cx="58" cy="188" rx="10" ry="5"/></g>
          <g class="bodyg">
            <path d="M34 50 Q50 42 66 50 L76 184 Q50 192 24 184 Z"/>
            <rect class="obi" x="33" y="88" width="34" height="20" rx="3"/>
            <circle cx="50" cy="28" r="15"/>
            <circle cx="60" cy="14" r="8"/>
            <g class="arm"><path class="armline" d="M44 58 L10 66"/></g>
          </g>
        </g>
      </svg>
    </div>
  </div>

</main>

<script>
(function () {{
  const frame   = document.getElementById('frame');
  const doorL   = document.getElementById('doorL');
  const person  = document.getElementById('person');
  const textBox = document.getElementById('text');

  const initialQuestion = {safe_q};
  const initialAnswer   = {safe_a};
  const hasAnswer       = {has_answer};

  // Tạo ô lưới nan gỗ Kumiko: 3 cột x 6 hàng
  document.querySelectorAll('.lattice').forEach(l => {{
    for (let i = 0; i < 18; i++) {{ const c = document.createElement('div'); c.className = 'cell'; l.appendChild(c); }}
  }});

  const wait = ms => new Promise(r => setTimeout(r, ms));
  const EASE = 'cubic-bezier(.45,.05,.55,.95)';
  let isOpen = false;

  const pw  = () => parseFloat(getComputedStyle(frame).getPropertyValue('--pw')) || 17.4;
  const tipOf = () => pw() * 0.40;

  function jump(x) {{
    person.style.transition = 'none';
    person.style.left = x + '%';
    void person.offsetWidth;
    person.style.transition = '';
  }}
  function glide(x, ms, ease) {{
    person.style.transition = `left ${{ms}}ms ${{ease || 'linear'}}, opacity .5s, filter .4s`;
    person.style.left = x + '%';
  }}

  /* ========= Mở cánh cửa TRÁI ========= */
  async function openDoor() {{
    const reachX = 48 + tipOf();
    person.className = 'person face-left';
    jump(reachX + 24);
    await wait(30);
    person.classList.add('shadow', 'walking');
    glide(reachX, 1800);
    await wait(1800);

    person.classList.remove('walking');
    person.classList.add('reach');
    await wait(700);

    const T = 2400;
    doorL.style.transition = `transform ${{T}}ms ${{EASE}}`;
    glide(reachX - 50, T, EASE);
    person.classList.add('walking');
    setTimeout(() => {{ person.classList.remove('shadow'); person.classList.add('clear'); }}, 500);
    doorL.style.transform = 'translateX(-100%)';
    await wait(T);

    person.classList.remove('walking', 'reach');
    await wait(300);
    person.classList.add('walking');
    glide(-18, 1300);
    await wait(800);
    person.classList.remove('clear');
    await wait(500);
    person.className = 'person face-left';
    isOpen = true;
  }}

  /* ========= Chữ hiện dần Thư Pháp ========= */
  async function reveal(question, answer) {{
    textBox.innerHTML = '';
    if (question && question.trim()) {{
      const q = document.createElement('div');
      q.className = 'q';
      q.textContent = '⛩️ Câu hỏi: ' + question;
      textBox.appendChild(q);
    }}

    const spans = [];
    String(answer).split(/\\n+/).forEach(par => {{
      const p = document.createElement('p');
      par.split(/\\s+/).filter(Boolean).forEach(word => {{
        const s = document.createElement('span');
        s.className = 'w';
        s.textContent = word;
        p.append(s, ' ');
        spans.push(s);
      }});
      textBox.appendChild(p);
    }});

    for (const s of spans) {{
      await wait(45);
      s.classList.add('on');
      textBox.scrollTop = textBox.scrollHeight;
    }}

    // Khi hoàn tất: Chờ 800ms để người đọc nhận biết xong, sau đó tự động cuộn êm về đầu văn bản
    if (textBox.scrollHeight > textBox.clientHeight) {{
      await wait(800);
      textBox.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}
  }}

  // Khởi động hoạt ảnh Thiền định Shoji
  async function startZenExperience() {{
    if (hasAnswer) {{
      await wait(400);
      await openDoor();
      await reveal(initialQuestion, initialAnswer);
    }} else {{
      // Trạng thái chờ: người đứng như bóng mờ tĩnh tại
      person.className = 'person face-left shadow';
      jump(65);
    }}
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', startZenExperience);
  }} else {{
    startZenExperience();
  }}
}})();
</script>
</body>
</html>"""
