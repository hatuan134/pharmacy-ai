# An Tâm — Hệ thống quản lý nhà thuốc có tích hợp AI

Mã nguồn ứng dụng chạy trên máy của bạn: **FastAPI + React + PostgreSQL + OpenAI**.
Giao diện tiếng Việt gồm 12 khu vực làm việc, có phân quyền ở cả giao diện và API.

**Đọc hướng dẫn từng bước dành cho Windows/VS Code:** [HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md).

## Chạy nhanh trong VS Code (Windows, terminal PowerShell)

Cần Python 3.12, Node.js 22 và Docker Desktop đang chạy. Giải nén toàn bộ dự án, mở thư mục `pharmacy-ai` trong VS Code.

Terminal thứ nhất — chuẩn bị PostgreSQL:

```powershell
py scripts/setup.py
docker compose up -d db
docker compose ps
```

Terminal thứ hai — backend (bắt đầu tại thư mục `pharmacy-ai`):

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.init_db
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Lệnh `app.init_db` yêu cầu bạn tự đặt mật khẩu tài khoản **admin**. Không có mật khẩu mặc định.

Terminal thứ ba — frontend (bắt đầu tại thư mục `pharmacy-ai`):

```powershell
cd frontend
npm ci
npm run dev
```

Mở **http://localhost:5173**, đăng nhập `admin` và mật khẩu đã đặt.
Giữ hai terminal backend và frontend hoạt động trong lúc sử dụng. Không mở trực tiếp `index.html`.

Nếu dùng PostgreSQL cài sẵn, có thể bỏ Docker; xem cách tạo database và cấu hình trong hướng dẫn chi tiết.

## Tính năng đã triển khai

| Nhóm | Chức năng |
|---|---|
| Tài khoản | Đăng nhập, đăng xuất, đổi mật khẩu, tạo nhân viên, khóa/mở tài khoản |
| Danh mục | Thêm/sửa/xóa thuốc, nhóm thuốc, đơn vị tính, nhà cung cấp; ngừng kinh doanh/hợp tác |
| Lô thuốc | Nhập lô, kiểm tra ngày/hạn, giá nhập/giá bán, theo dõi tồn từng lô, thay đổi giá bán |
| Kiểm kê | Điều chỉnh số lượng thực tế với lý do, phát hiện dữ liệu tồn đã thay đổi, nhật ký biến động |
| Bán hàng | Tìm theo tên/mã/lô, danh sách lô theo hạn gần nhất, giỏ hàng, tiền mặt/chuyển khoản, hóa đơn và bản in |
| Toàn vẹn tồn | Giao dịch nguyên tử, khóa dòng lô, chống gửi thanh toán lặp, hoàn kho khi hủy toàn bộ hóa đơn |
| Hạn dùng | Chặn bán lô có HSD ≤ hôm nay; cảnh báo theo khoảng ngày; cảnh báo tồn bán được dưới ngưỡng |
| Tra cứu | Tìm thuốc, tìm số lô, lọc nhóm và hạn dùng |
| Báo cáo | Doanh thu theo ngày/khoảng ngày, số hóa đơn, giá trị tồn theo giá nhập, danh sách cảnh báo |
| AI | Tóm tắt bằng trích chọn nguồn thuốc đã duyệt, điểm cần chú ý về hạn dùng, hỏi đáp quy trình đã duyệt |
| Quản trị AI | Duyệt nguồn; sửa nội dung tự hủy trạng thái duyệt; log yêu cầu/kết quả/nguồn/cảnh báo |

Tồn và giá lưu theo **lô**, tiền dùng `Decimal`/`Numeric`. Thuốc kê đơn chỉ được quản lý/dược sĩ lập hóa đơn sau khi kiểm tra và nhập mã đơn; thu ngân bị chặn ở backend. Ứng dụng chỉ lưu mã tham chiếu, không xác thực tính hợp lệ của đơn thuốc ngoài đời.

## OpenAI

Mở `backend/.env` (được tạo bằng `scripts/setup.py`):

```dotenv
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4.1-mini
```

Khởi động lại backend. Key chỉ nằm ở backend, không đưa vào React hoặc Git. Model cấu hình được và phải khả dụng trong tài khoản API của bạn. Khi thiếu key, hết hạn mức, lỗi mạng hay lỗi model, giao diện báo lỗi rõ ràng; các chức năng quản lý khác vẫn dùng được.

Tích hợp bằng OpenAI Python SDK, Responses API và Structured Outputs. Model chỉ chọn các ID nguồn; server kiểm tra ID và ghép nội dung nguyên văn. Đây là tóm tắt **trích chọn**, không sinh hướng dẫn dùng thuốc tự do. Đề xuất xử lý lô lấy từ quy tắc của phần mềm, AI chọn các lô đáng chú ý. Không có công cụ cho AI ghi hoặc sửa tồn kho. [Tài liệu Structured Outputs chính thức](https://developers.openai.com/api/docs/guides/structured-outputs).

## Cấu trúc dự án

```text
pharmacy-ai/
  backend/
    app/
      main.py          API, phân quyền, CRUD, báo cáo
      models.py        Mô hình quan hệ và ràng buộc dữ liệu
      schemas.py       Kiểm tra đầu vào
      services.py      Giao dịch bán hàng, hủy đơn, tồn kho
      auth.py          Hash mật khẩu, phiên đăng nhập
      ai.py            Prompt, OpenAI, kiểm tra nguồn, log
      config.py        Biến môi trường, ngày nghiệp vụ
      db.py            Kết nối và phiên SQLAlchemy
      init_db.py       Khởi tạo schema và tài khoản quản lý
      seed.py          Dữ liệu luyện tập tùy chọn
    tests/             Kiểm thử API và PostgreSQL đồng thời
    requirements.txt
  frontend/
    src/main.jsx       Màn hình và thành phần React
    src/style.css      Giao diện thích ứng
    src/api.js         Gọi API, xử lý lỗi/phiên đăng nhập
    src/ui.test.jsx    Kiểm thử tương tác giao diện
    package-lock.json
  docs/                Thiết kế, SDLC, phạm vi kiểm thử
  scripts/setup.py     Tạo cấu hình và bí mật cục bộ
  compose.yaml         PostgreSQL với volume lưu dữ liệu
  HUONG_DAN_CHAY.md
```

## Kiểm thử

Backend, tại thư mục `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend, tại thư mục `frontend`:

```powershell
npm test
npm run build
```

Kiểm thử đơn vị/API dùng SQLite tạm trong bộ nhớ. Kiểm thử riêng PostgreSQL cần `TEST_POSTGRES_URL` trỏ đến **database kiểm thử riêng**; xem `docs/KIEM_THU.md`. Không dùng SQLite để thay PostgreSQL khi vận hành nhiều người dùng.

## Phạm vi phiên bản bàn giao

Đây là phiên bản cho đồ án và chạy thử cục bộ. Có đầy đủ luồng quản lý chính, nhưng chưa tích hợp hóa đơn điện tử, thanh toán ngân hàng, mã vạch phần cứng, nhiều chi nhánh, quy đổi hộp/vỉ/viên, trả hàng một phần hay lưu ảnh đơn thuốc. Thanh toán chuyển khoản là ghi nhận phương thức sau khi nhân viên xác nhận đã nhận tiền; ứng dụng không tự chuyển tiền hoặc kiểm tra ngân hàng.

Không tự nạp dữ liệu thuốc thật. Không được coi dữ liệu luyện tập là thông tin dược phẩm. Thông tin chuyên môn và quy trình phải được người có trách nhiệm rà soát trước khi duyệt. Xem giới hạn AI và vận hành trong `docs/THIET_KE.md`.
