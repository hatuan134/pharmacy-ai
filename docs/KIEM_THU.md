# Kiểm thử và trạng thái xác minh

## Kết quả thực tế khi tạo bản bàn giao

| Hạng mục | Kết quả |
|---|---|
| Backend/API: `python -m pytest -q` | **28 passed, 1 skipped** |
| React: `npm test` | **13 passed** |
| Frontend: `npm run build` | **Thành công** |
| Biên dịch DDL cho PostgreSQL | **11 bảng**, không lỗi biên dịch |
| Khởi tạo CSDL và seed qua CLI | Đã chạy trên SQLite phục vụ kiểm thử cục bộ |
| OpenAI SDK/Structured Outputs | Đã kiểm thử qua HTTP MockTransport với SDK thật |
| Gọi OpenAI bằng API key thật | **Chưa thực hiện**, không có key người dùng |
| Chạy ứng dụng trên PostgreSQL thật | **Chưa thực hiện trong môi trường tạo dự án** |
| Kiểm thử đồng thời PostgreSQL | Có sẵn test, **bỏ qua vì thiếu TEST_POSTGRES_URL** |
| Kiểm tra giao diện qua trình duyệt | **Chưa hoàn tất**: trình duyệt chặn localhost (`ERR_BLOCKED_BY_CLIENT`) |

Các test React dùng jsdom/Testing Library và API mock. Chúng kiểm tra render, thao tác và payload, không thay thế kiểm tra trình duyệt đầy đủ. Các test API dùng SQLAlchemy với SQLite in-memory, không chứng minh khóa dòng hoặc mức cô lập PostgreSQL. DDL được biên dịch cho PostgreSQL nhưng chưa áp dụng lên server PostgreSQL trong phiên này.

Có một cảnh báo deprecation từ Starlette/TestClient với AnyIO ở môi trường kiểm thử; không có kiểm thử thất bại.

## Phạm vi test backend

- Đăng nhập đúng/sai, phiên sau đăng xuất và tài khoản khóa.
- Header chống CSRF/origin không hợp lệ.
- Nhập lô, trùng lô, ngày nhập tương lai, lô đã hết hạn, số lượng/giá không hợp lệ.
- Bán hàng trừ kho, lưu giá lịch sử.
- Thiếu tồn và nhiều lô: kiểm tra rollback không để hóa đơn/tồn sai.
- Dòng lặp cùng lô được tính tổng.
- Gửi lặp request giữ một hóa đơn; request key trùng nhưng dữ liệu khác bị từ chối.
- Hết hạn đúng hôm nay bị chặn; không xuất hiện ở quầy.
- Cảnh báo tồn thấp chỉ tính tồn có thể bán.
- Hủy đơn hoàn kho một lần, loại khỏi doanh thu.
- Kiểm kê có xung đột tồn và có sổ biến động.
- Thuốc kê đơn yêu cầu quyền và mã đơn tham chiếu.
- Thu ngân không xem hóa đơn của người khác hoặc hủy đơn.
- Sửa dữ liệu thu hồi duyệt; FK chặn xóa dữ liệu đã được dùng.
- AI chặn một số câu hỏi lâm sàng/tấn công, không gọi provider khi bị chặn.
- AI chỉ đọc nguồn đã duyệt, ghép đúng đoạn nguồn và cảnh báo.
- Thiếu key, không có dữ liệu, nguồn chưa duyệt, ID nguồn bịa.
- Lỗi provider được đổi thành thông báo rõ ràng và lưu log, không lộ lỗi thô.
- OpenAI SDK gửi đúng `/v1/responses`, schema JSON, `store=False`; parse phản hồi có cấu trúc.
- Báo cáo khoảng ngày ngược và đổi đơn vị của thuốc đã có lô.
- Giá đã thay đổi sau khi thêm giỏ cần xác nhận lại, không tự tính tiền theo giá mới.

## Phạm vi test React

- Dashboard và nút điều hướng bán hàng.
- Trang thuốc: tải dữ liệu, sửa tên, chỉ gửi các trường được phép ghi.
- POS: thêm lô, gửi đúng số lượng/giá kỳ vọng; request key giữ nguyên khi retry mất mạng.
- Thu ngân không chọn được sản phẩm kê đơn.
- Lô nhập: hiện tồn và mở form kiểm kê.
- Hóa đơn trống, cảnh báo, báo cáo chưa có doanh thu.
- AI báo thiếu key mà màn hình vẫn thao tác được; hiển thị kết quả như text, không thực thi HTML.
- Nhân viên, thiết lập mật khẩu, API lỗi có nút thử lại.

## Chạy test trên máy bạn

Backend, tại `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend, tại `frontend`:

```powershell
npm test
npm run build
```

## Test đồng thời trên PostgreSQL

1. Tạo một database **kiểm thử riêng**, ví dụ `pharmacy_test`, chủ sở hữu là tài khoản chạy test.
2. Không trỏ test vào database vận hành.
3. Tại terminal PowerShell ở `backend`:

```powershell
$env:TEST_POSTGRES_URL="postgresql+psycopg://pharmacy:MAT_KHAU_DB@localhost:5432/pharmacy_test"
.\.venv\Scripts\python.exe -m pytest -q -m postgres
```

Test tạo schema ngẫu nhiên `pharmacy_test_<uuid>`, thêm một lô 10 đơn vị và hai người bán. Hai luồng cùng mua 7 đơn vị. Kỳ vọng: một giao dịch thành công, một giao dịch HTTP 409, tồn còn 3, chỉ một hóa đơn. Schema test được dọn trong `finally`; nếu tiến trình bị kill có thể còn schema cần quản trị viên dọn sau khi kiểm tra.

Với Git Bash:

```bash
export TEST_POSTGRES_URL='postgresql+psycopg://pharmacy:MAT_KHAU_DB@localhost:5432/pharmacy_test'
./.venv/Scripts/python.exe -m pytest -q -m postgres
```

## Checklist nghiệm thu thủ công còn cần chạy

| Thao tác | Kết quả mong đợi |
|---|---|
| Khởi tạo PostgreSQL, admin, frontend/backend | Đăng nhập được qua cổng 5173 |
| Tạo nhóm → đơn vị → NCC → thuốc → lô | Lô mới có tồn đúng số lượng và có log nhập |
| Hai cửa sổ/phiên cùng bán lô ít tồn | Không âm kho; một giao dịch bị chặn nếu tổng vượt tồn |
| Đổi giá trong lúc giỏ đã có thuốc | Quầy nhận HTTP 409, nhân viên phải tải lại thuốc |
| Hủy hóa đơn hai lần | Tồn chỉ hoàn một lần |
| In hóa đơn | Không in sidebar/nút thao tác; tổng khớp chi tiết |
| Thu ngân thử sửa lô/xem hóa đơn người khác | Backend từ chối 403 |
| Duyệt quy trình và gọi OpenAI thật | Có kết quả, nguồn, cảnh báo và log; kiểm tra tính phù hợp |
| API key sai hoặc mất mạng | Báo lỗi rõ, chức năng quản lý vẫn hoạt động |
| Xem bằng cửa sổ hẹp/điện thoại | Menu mở được, bảng cuộn ngang, form không tràn |

Đây là checklist **chưa được đánh dấu hoàn tất**; nhóm cần ghi kết quả/ảnh chụp thực tế khi chạy trên máy và PostgreSQL của mình.
