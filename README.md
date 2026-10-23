<<<<<<< HEAD
# HouseAssist: AI Real Estate Advisor & Analytics Agent
**Dự án Capstone Học kỳ 1 (Semester 1 Project) - Jetking ADAI**  
*Ứng dụng Trợ lý AI Bất động sản King County (Seattle & vùng phụ cận) tích hợp Machine Learning, OpenRouter LLM, Tool Calling và Stateful Memory trên Streamlit UI.*

---

## 1. Tổng Quan Dự Án (Project Overview)
- **Bài toán nghiệp vụ**: Định giá bất động sản, phân tích thống kê thị trường và phân khúc nhà ở thường đòi hỏi tính toán số liệu chính xác kết hợp với khả năng diễn giải ngôn ngữ tự nhiên. 
- **Giải pháp**: Xây dựng ứng dụng **HouseAssist** theo mô hình Single-Model Agentic Architecture (chuẩn Jetking SkyAssist pattern). Hệ thống cho phép người dùng hỏi đáp tự nhiên; Agent tự động nhận diện ý định, gọi các công cụ Machine Learning (Random Forest) và thống kê dữ liệu (Pandas, K-Means), sau đó tổng hợp câu trả lời chuyên sâu.

---

## 2. Kiến Trúc Hệ Thống (Schematic Diagram)

```
[ Người dùng / Trình duyệt ]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                │
│  - Khung chat tương tác (st.chat_message, chat_input)   │
│  - Cấu hình OpenRouter API Key & chọn mô hình           │
│  - Bảng Dashboard tóm tắt số liệu thị trường           │
│  - Tool Execution Inspection (Hiển thị chi tiết tool)  │
└───────────────────────────┬────────────────────────────┘
                            │ (User message & History)
                            ▼
┌────────────────────────────────────────────────────────┐
│             Agent Orchestrator (agent.py)              │
│  - Quản lý System Prompt & ngữ cảnh (Stateful Memory)  │
│  - Giao tiếp OpenRouter Gateway (model: openrouter/free)│
│  - Tool Schema & Function Calling Execution Loop       │
│  - Chế độ Heuristic Fallback khi không có API key      │
└───────────────────────────┬────────────────────────────┘
                            │ (Tool Calls & Arguments)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Bộ Công Cụ Nghiệp Vụ (tools.py)          │
│  1. predict_house_price: Dự đoán giá bán (USD)         │
│  2. get_market_statistics: Thống kê số liệu thị trường │
│  3. segment_house: Phân khúc K-Means 3 tầng            │
│  4. find_similar_houses: Tìm kiếm căn nhà tương đồng   │
│  5. explain_price_factors: Giải thích Feature Import.  │
└───────────────────────────┬────────────────────────────┘
                            │ (Data Queries & Predictions)
                            ▼
┌────────────────────────────────────────────────────────┐
│              Data & Machine Learning Engine (data.py)  │
│  - Bộ dữ liệu sạch 4,548 căn (đã xử lý giá 0, typo)   │
│  - Random Forest Regressor (R² ≈ 0.72, MAE ≈ $98k)     │
│  - K-Means Clustering (k=3, Silhouette = 0.361)        │
│  - Nearest Neighbors (KNN) tính độ tương đồng          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Danh Mục Công Cụ (Tool Catalog)

| Tên Công Cụ | Tham Số Đầu Vào (Input) | Dữ Liệu Trả Về (Output) | Phạm Vi An Toàn (Safe Scope) |
| :--- | :--- | :--- | :--- |
| `predict_house_price` | `sqft_living`, `city`, `bedrooms`, `bathrooms`, `sqft_lot`, `yr_built`... | Giá dự đoán điểm (USD), khoảng tin cậy 90%, đơn giá/sqft | Dự đoán suy diễn từ mô hình ML đã train |
| `get_market_statistics` | `city` (tùy chọn: để trống là toàn vùng) | Số lượng giao dịch, giá trung vị, min/max, top thành phố | Đọc và tổng hợp thống kê từ `data.csv` |
| `segment_house` | `price`, `sqft_living` | Phân khúc (Bình dân / Trung cấp / Cao cấp), mô tả thị trường | Phân loại dựa trên K-Means tâm cụm |
| `find_similar_houses` | `city`, `target_price`, `bedrooms`, `sqft_living`, `max_results` | Danh sách 3 căn nhà thực tế gần nhất trong tập dữ liệu | Truy vấn không gian Euclidean khoảng cách |
| `explain_price_factors` | Không có | Top 10 đặc trưng quan trọng nhất và kết luận phân tích | Trích xuất Feature Importance từ Random Forest |

---

## 4. Hướng Dẫn Cài Đặt & Khởi Chạy (Quickstart)

### 4.1. Cài đặt môi trường
Yêu cầu: Python 3.10+ (Đã kiểm nghiệm tốt trên Python 3.11, 3.12, 3.14).

```bash
# 1. Di chuyển vào thư mục dự án
cd "path/to/ass1"

# 2. Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 4.2. Cấu hình Khóa API (Tùy chọn)
- Cách 1: Nhập trực tiếp trên ô **OpenRouter API Key** ở thanh Sidebar khi ứng dụng đang chạy.
- Cách 2: Tạo file `.streamlit/secrets.toml` từ mẫu `.streamlit/secrets.toml.example`:
  ```toml
  OPENROUTER_API_KEY = "sk-or-v1-YOUR_KEY"
  ```
- *Lưu ý*: Nếu không có API Key, hệ thống tự động kích hoạt **Chế độ Phân tích Ngoại tuyến (Heuristic Analytics Mode)** vẫn đảm bảo gọi được đầy đủ 5 công cụ mà không bị gián đoạn.

### 4.3. Khởi chạy ứng dụng Web
```bash
streamlit run app.py
```
Trình duyệt sẽ tự động mở giao diện tại địa chỉ: `http://localhost:8501`.

---

## 5. Kiểm Thử Hệ Thống (Testing & Test Cases)

Hệ thống đi kèm bộ kiểm thử tự động kiểm tra tính đúng đắn của 5 công cụ:
```bash
python -m unittest tests/test_tools.py
```

### Bảng Kịch Bản Kiểm Thử (Test Cases Matrix):
| Mã TC | Câu hỏi người dùng mẫu (User Prompt) | Hành vi kỳ vọng của Agent | Kết quả |
| :---: | :--- | :--- | :---: |
| **TC01** | *"Thống kê thị trường tại thành phố Seattle?"* | Gọi `get_market_statistics(city='Seattle')`, trả về trung vị, min/max và giao dịch. | **PASS** |
| **TC02** | *"Dự đoán giá căn nhà 2,000 sqft, 3 phòng ngủ ở Bellevue?"* | Gọi `predict_house_price(...)`, trả về giá USD và khoảng dao động tin cậy. | **PASS** |
| **TC03** | *(Follow-up)* *"Thế căn nhà đó thuộc phân khúc nào?"* | Nhớ ngữ cảnh căn vừa tính, gọi `segment_house` xác định phân khúc K-Means. | **PASS** |
| **TC04** | *"Tìm cho tôi 3 căn nhà tương tự tại Bellevue?"* | Gọi `find_similar_houses(city='Bellevue')`, trả về địa chỉ và giá thật trong dữ liệu. | **PASS** |
| **TC05** | *"Yếu tố nào tác động mạnh nhất đến giá nhà?"* | Gọi `explain_price_factors()`, giải thích tỉ trọng của diện tích, vị trí và năm xây. | **PASS** |
| **TC06** | *"Cho tôi giá nhà ở thành phố Paris (ngoài King County)?"* | Xử lý ngoại lệ lịch sự, thông báo phạm vi dữ liệu và gợi ý các thành phố lân cận. | **PASS** |

---

## 6. Tiêu Chí Đánh Giá Dự Án (Evaluation Checklist)
- [x] **Kiến trúc hệ thống chuẩn mực**: Phân tách rõ ràng giữa UI (`app.py`), Agent (`agent.py`), Tools (`tools.py`) và Dữ liệu (`data.py`).
- [x] **Tích hợp OpenRouter & Tool Calling**: Áp dụng chuẩn Function Calling của OpenAI/OpenRouter với schema tham số rõ ràng.
- [x] **Bộ công cụ giá trị cao**: Kết hợp cả mô hình học máy giám sát (Random Forest) và không giám sát (K-Means).
- [x] **Trải nghiệm người dùng cao cấp**: Có hiển thị Tool Execution Inspection để giảng viên kiểm tra minh bạch từng lời gọi hàm.
- [x] **Xử lý ngoại lệ an toàn**: Có cơ chế Fallback thông minh giúp hệ thống luôn hoạt động mượt mà.
=======
# AI_PROJECT_TEAM
>>>>>>> 5a38567682f415022c76db820be4fe9693ffb6ea
