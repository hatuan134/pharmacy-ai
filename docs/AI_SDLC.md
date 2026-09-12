# Sử dụng AI trong SDLC — minh chứng và mẫu tái lập

## Bằng chứng đã có trong gói này

Yêu cầu đầu vào thực tế của người dùng: xây dựng hệ thống nhà thuốc quản lý thuốc, nhóm, đơn vị, lô, HSD, giá, bán hàng/hóa đơn, cảnh báo, NCC, tìm kiếm, báo cáo; dùng FastAPI, React, PostgreSQL và OpenAI; có test cho lô, hạn, bán hàng và AI.

Trong phiên tạo dự án, trợ lý AI đã sinh mã nguồn, test và tài liệu. Các quyết định như khóa lô, chống thanh toán lặp, hoàn kho một lần, thu hồi trạng thái duyệt và chọn nguồn trích dẫn được hiện thực trực tiếp trong mã.

| Giai đoạn | Đầu vào / yêu cầu | Đầu ra có thể kiểm chứng |
|---|---|---|
| Phân tích | Yêu cầu gốc của đề tài | README tính năng, bảng vai trò và quy tắc trong THIET_KE.md |
| Thiết kế | Tồn kho theo lô, bảo toàn hóa đơn, giới hạn AI | models.py, schemas.py, ERD và mô tả transaction |
| Lập trình | FastAPI + React + PostgreSQL + OpenAI | backend/app, frontend/src, compose.yaml |
| Kiểm thử | Hết hạn, thiếu tồn, lặp giao dịch, phân quyền, AI không có nguồn | backend/tests, frontend/src/ui.test.jsx, KIEM_THU.md và log test |
| Triển khai | Người dùng chạy VS Code trên Windows | scripts/setup.py, README.md, HUONG_DAN_CHAY.md |
| Bảo trì | Tìm nguyên nhân lỗi màn hình / kho / AI | Bảng lỗi thường gặp, nhật ký biến động và nhật ký AI |

**Không coi các prompt mẫu dưới đây là nhật ký những lần gọi AI độc lập đã thực sự diễn ra.** Chúng là bộ prompt tái lập để nhóm sinh viên sử dụng và tự lưu phản hồi, commit, ảnh chụp, kết quả kiểm thử của chính nhóm.

## Prompt mẫu theo từng giai đoạn

### 1. Phân tích yêu cầu

- Role: Bạn là BA cho hệ thống quản lý nhà thuốc.
- Context: 3 vai trò quản lý, dược sĩ, thu ngân; quản lý tồn kho theo lô; AI chỉ tra cứu nội bộ.
- Task: Viết use case cho nhập lô, bán hàng, hủy đơn, kiểm kê và duyệt nguồn AI.
- Constraints: Nêu điều kiện trước/sau, luồng chính/ngoại lệ và phân quyền; không giả định AI có quyền kê đơn.
- Output: Bảng ID, actor, trigger, input, xử lý, output, lỗi, tiêu chí nghiệm thu.

### 2. Thiết kế

- Role: Bạn là kiến trúc sư CSDL và backend.
- Context: FastAPI/SQLAlchemy/PostgreSQL; giá và tồn nằm trên lô, không trên thuốc.
- Task: Thiết kế schema và transaction bán hàng/hủy đơn.
- Constraints: Tiền Decimal, tồn không âm; FK/UNIQUE/CHECK; hai thu ngân không bán vượt tồn; retry không tạo hóa đơn mới.
- Output: ERD, mô hình bảng, thứ tự khóa, điểm commit/rollback và rủi ro đồng thời.

### 3. Sinh code

- Role: Bạn là lập trình viên full-stack.
- Context: API trong app/main.py, schema trong app/schemas.py, frontend dùng React qua /api.
- Task: Tạo form thuốc/lô, POS, hóa đơn, cảnh báo và AI có trạng thái đang tải/lỗi/rỗng.
- Constraints: Gọi API thật, xử lý HTTP 401/403/409/422; không đưa key vào frontend; không tự giả lập phản hồi OpenAI khi thiếu key.
- Output: File thay đổi, cách chạy và bằng chứng kiểm thử.

### 4. Kiểm thử và debug tồn kho

- Role: Bạn là QA/backend reviewer.
- Context: Luồng create_sale và cancel_sale ở app/services.py.
- Task: Tìm lỗi bán âm kho, hủy lặp, giá bị đổi khi thanh toán, nhiều dòng cùng lô và request bị retry.
- Constraints: Test phải kiểm tra trạng thái CSDL sau lỗi, không chỉ HTTP code; test PostgreSQL thật cho khóa dòng; không dùng SQLite để chứng minh concurrency.
- Output: Test thất bại trước sửa, bản sửa, test đạt sau sửa và giới hạn còn lại.

### 5. Kiểm thử AI

- Role: Bạn là kiểm thử viên an toàn AI.
- Context: Model chỉ chọn ID nguồn; server ghép nguyên văn; nguồn phải được duyệt.
- Task: Kiểm tra câu hỏi kê đơn/liều, prompt injection, ID nguồn bịa, dữ liệu chưa duyệt, thiếu key và provider trả lỗi.
- Constraints: Không gọi model thật khi test đơn vị; tách kiểm thử model thật và ghi rõ trạng thái; không tuyên bố bộ lọc tuyệt đối an toàn.
- Output: Bộ test, log, lỗi cần sửa và điều kiện cần người duyệt.

### 6. Triển khai và bảo trì

- Role: Bạn là người hướng dẫn triển khai cho sinh viên.
- Context: Windows, VS Code, PowerShell/Git Bash, PostgreSQL Docker hoặc cài sẵn.
- Task: Viết từng bước từ giải nén đến đăng nhập, nhập lô, bán, AI và test.
- Constraints: Mật khẩu người dùng tự đặt; không commit .env; không có lệnh xóa volume trong quy trình chạy bình thường.
- Output: Hướng dẫn thực hành, bảng lỗi thường gặp và cách khôi phục an toàn.

## Nhật ký nhóm cần bổ sung khi nộp đồ án

| Ngày | Người thực hiện | Giai đoạn | Prompt / tệp đính kèm | Phản hồi AI | Điều chỉnh của người làm | Commit / test / ảnh |
|---|---|---|---|---|---|---|
| Nhóm tự điền | Nhóm tự điền | Ví dụ KT2 | Lưu prompt nguyên văn | Lưu phản hồi nguyên văn | Mô tả sửa | Dẫn đến minh chứng thật |

Không tự gán tác giả, ngày thực hiện hoặc kết quả triển khai chưa xảy ra. AI hỗ trợ tạo code; nhóm phải đọc, chạy, kiểm tra chuyên môn và chịu trách nhiệm nghiệm thu.
