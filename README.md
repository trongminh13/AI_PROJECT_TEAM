# HouseAssist: AI Real Estate Advisor & Analytics Agent
**Dự án Capstone Học kỳ 1 (Semester 1 Project) - Jetking ADAI**  
*Ứng dụng Trợ lý AI Bất động sản Việt Nam (Hà Nội, TP. Hồ Chí Minh, Đà Nẵng & toàn quốc) tích hợp Machine Learning, OpenRouter LLM, Tool Calling và Stateful Memory trên Streamlit UI.*

---

## 1. Tổng Quan Dự Án (Project Overview)
- **Bài toán nghiệp vụ**: Định giá bất động sản, phân tích thống kê thị trường và phân khúc nhà ở tại Việt Nam đòi hỏi tính toán số liệu chính xác (Tỷ VNĐ, diện tích m², đơn giá triệu/m², các khoảng cách đô thị) kết hợp với khả năng diễn giải ngôn ngữ tự nhiên thông minh.
- **Giải pháp**: Xây dựng ứng dụng **HouseAssist** theo mô hình Single-Model Agentic Architecture (chuẩn Jetking SkyAssist pattern). Hệ thống cho phép người dùng tương tác tự nhiên qua giao diện Trà Thất Shoji; Agent tự động nhận diện ý định, gọi các công cụ Machine Learning (Random Forest Regressor, K-Means Clustering) và trích xuất dữ liệu đa nguồn, sau đó tổng hợp câu trả lời chuyên sâu.

---

## 2. Kiến Trúc Hệ Thống (Schematic Diagram)

```
[ Người dùng / Trình duyệt ]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                │
│  - Không gian Thiền Định Shoji & Chữ Thư Pháp Loang Mờ │
│  - 4 Cuộn Thư Gợi Ý Cổ Xưa (Native Button Overlay)     │
│  - Bảng Dashboard chỉ số thị trường Việt Nam           │
│  - Khám phá 4 Phân khúc K-Means & Lăng kính Đô thị     │
│  - Cấu hình OpenRouter Gateway & Chế độ Offline        │
└───────────────────────────┬────────────────────────────┘
                            │ (User message & History)
                            ▼
┌────────────────────────────────────────────────────────┐
│             Agent Orchestrator (agent.py)              │
│  - Quản lý System Prompt & ngữ cảnh (Stateful Memory)  │
│  - Giao tiếp OpenRouter Gateway (model: openrouter/free)│
│  - Tool Schema chuẩn OpenAI Function Calling Loop      │
│  - Bộ điều phối Heuristic Fallback khi không có API key│
└───────────────────────────┬────────────────────────────┘
                            │ (Tool Calls & Arguments)
                            ▼
┌────────────────────────────────────────────────────────┐
│               Bộ Công Cụ Nghiệp Vụ (tools.py)          │
│  1. predict_house_price: Dự đoán giá bán (Tỷ VNĐ)      │
│  2. get_market_statistics: Thống kê số liệu thị trường │
│  3. segment_house: Phân khúc K-Means 4 tầng            │
│  4. find_similar_houses: Tìm kiếm căn nhà thực tế      │
│  5. explain_price_factors: Giải thích Feature Import.  │
└───────────────────────────┬────────────────────────────┘
                            │ (Data Queries & Predictions)
                            ▼
┌────────────────────────────────────────────────────────┐
│              Kiến Trúc Dữ Liệu Dual-Source (data.py)   │
│  - housing_clean.csv (9,714 dòng sạch 100%, 0 Null)   │
│    -> Random Forest Regressor (R² ≈ 0.81)              │
│    -> K-Means 4 Clusters (Bình dân, Trung, Cao, Sang)  │
│  - house_cleaned.csv (30,078 dòng listing thực tế)     │
│    -> Tìm nhà tương đồng theo địa chỉ, dự án thật      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Danh Mục Công Cụ (Tool Catalog)

| Tên Công Cụ | Tham Số Đầu Vào (Input) | Dữ Liệu Trả Về (Output) | Phạm Vi Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `predict_house_price` | `land_area` (m²), `province`, `bedrooms`, `bathrooms`, `floors`, `distance_to_center`... | Giá dự đoán điểm (Tỷ VNĐ), khoảng dao động tin cậy (88–112%), đơn giá triệu/m² | Suy diễn từ mô hình Random Forest Regressor đã huấn luyện trên 9,714 giao dịch sạch |
| `get_market_statistics` | `province` (tùy chọn: để trống là toàn quốc) | Số lượng giao dịch, giá trung vị, giá trung bình, min/max, đơn giá/m² | Đọc và tổng hợp thống kê từ `housing_clean.csv` |
| `segment_house` | `price_billion_vnd`, `land_area_m2` | Phân khúc (Bình dân / Trung cấp / Cao cấp / Hạng sang), hồ sơ thị trường | Phân loại dựa trên thuật toán K-Means tâm cụm chuẩn hóa |
| `find_similar_houses` | `province`, `target_price_billion`, `bedrooms`, `land_area_m2`, `max_results` | Danh sách các căn nhà thực tế với địa chỉ thật, tên dự án Vinhomes thật | Truy vấn không gian Euclidean khoảng cách từ `house_cleaned.csv` (30,078 dòng) |
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
- Cách 1: Nhập trực tiếp trên ô **OpenRouter API Key** ở Tab Cài Đặt trên giao diện.
- Cách 2: Tạo file `.env` hoặc cấu hình biến môi trường:
  ```bash
  export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY"
  ```
- *Lưu ý*: Nếu không có API Key, hệ thống tự động kích hoạt **Chế độ Phân tích Ngoại tuyến (Heuristic Analytics Mode)**, vẫn gọi và chạy đầy đủ 5 công cụ Machine Learning cục bộ mà không bị gián đoạn.

### 4.3. Khởi chạy ứng dụng Web
```bash
streamlit run app.py
```
Trình duyệt sẽ tự động mở giao diện tại địa chỉ: `http://localhost:8501`.

---

## 5. Kiểm Thử Hệ Thống (Testing & Test Cases)

Hệ thống đi kèm bộ kiểm thử tự động kiểm tra tính đúng đắn của toàn bộ 5 công cụ:
```bash
pytest tests/test_tools.py -v
```

### Bảng Kịch Bản Kiểm Thử (Test Cases Matrix):
| Mã TC | Câu hỏi người dùng mẫu (User Prompt) | Hành vi kỳ vọng của Agent | Kết quả |
| :---: | :--- | :--- | :---: |
| **TC01** | *"Dự đoán giá căn nhà phố 80m² tại Hà Nội?"* | Gọi `predict_house_price(...)`, trả về giá Tỷ VNĐ và khoảng dao động tin cậy. | **PASS** |
| **TC02** | *"Thống kê thị trường tại Đà Nẵng?"* | Gọi `get_market_statistics(province='Đà Nẵng')`, trả về trung vị, min/max, số lượng căn. | **PASS** |
| **TC03** | *"Phân khúc căn nhà 1.2 tỷ 60m² và căn 25 tỷ 300m²?"* | Gọi `segment_house(...)`, phân loại chính xác Bình dân (0) và Hạng sang (3). | **PASS** |
| **TC04** | *"Tìm cho tôi 3 căn nhà tương tự tại Hà Nội giá khoảng 3.5 tỷ?"* | Gọi `find_similar_houses(...)`, trả về địa chỉ thật và tên dự án từ `house_cleaned.csv`. | **PASS** |
| **TC05** | *"Yếu tố nào tác động mạnh nhất đến giá nhà tại Việt Nam?"* | Gọi `explain_price_factors()`, giải thích tỉ trọng của diện tích đất, vị trí và khoảng cách. | **PASS** |
| **TC06** | *"Cho tôi giá nhà ở tỉnh không tồn tại?"* | Xử lý ngoại lệ lịch sự, thông báo trạng thái `not_found` kèm danh sách tỉnh/thành gợi ý. | **PASS** |

---

## 6. Tiêu Chí Đánh Giá Dự Án (Evaluation Checklist)
- [x] **Kiến trúc hệ thống chuẩn mực**: Phân tách rõ ràng giữa UI (`app.py`), Agent (`agent.py`), Tools (`tools.py`) và Dữ liệu Dual-Source (`data.py`).
- [x] **Tích hợp OpenRouter & Tool Calling**: Áp dụng chuẩn Function Calling của OpenAI/OpenRouter với schema tham số Việt Nam rõ ràng.
- [x] **Mô hình học máy chuẩn xác**: Kết hợp cả mô hình học máy giám sát (Random Forest Regressor) và không giám sát (K-Means 4 tầng).
- [x] **Trải nghiệm người dùng độc bản**: Không gian Thiền Định Shoji kết hợp cuộn thư cổ xưa với công nghệ Native Button Overlay đạt chuẩn Zero-Reload WebSocket.
- [x] **Xử lý ngoại lệ an toàn**: Có cơ chế Heuristic Fallback thông minh giúp hệ thống luôn phản hồi mượt mà ngay cả khi không có kết nối Internet.
