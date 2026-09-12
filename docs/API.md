# API và kiểm tra nhanh

Mọi URL dưới đây có prefix `/api`. Xem OpenAPI tại `http://localhost:8000/docs` sau khi chạy backend.

- Phiên đăng nhập dùng cookie `session` HttpOnly, không phải Bearer token.
- Yêu cầu ghi phải có header `X-Requested-With: pharmacy`.
- Swagger hiển thị header này; để giá trị `pharmacy`. Dùng `/auth/login` trong cùng Swagger để nhận cookie, rồi gọi các endpoint tiếp theo.
- `GET /health` không yêu cầu đăng nhập.
- Lỗi trả `{"detail":"Thông báo"}` hoặc mảng chi tiết validation. React đã xử lý cả hai kiểu.

| Endpoint | Phương thức | Ý nghĩa |
|---|---|---|
| /auth/login | POST | username, password → phiên đăng nhập |
| /auth/me | GET | Người đang đăng nhập |
| /auth/logout | POST | Hủy phiên cũ |
| /auth/password | POST | Đổi mật khẩu cá nhân |
| /users | GET/POST | Danh sách/tạo tài khoản (quản lý) |
| /users/{id} | PATCH | Khóa/mở tài khoản |
| /medicines, /categories, /units, /suppliers, /procedures | GET/POST | Danh sách/thêm |
| Các danh mục ở trên + /{id} | PUT/DELETE | Cập nhật/xóa, kiểm tra quyền và FK |
| /medicines/{id}/approve, /procedures/{id}/approve | POST | Duyệt nguồn AI |
| /batches | GET/POST | Tìm/nhập lô |
| /batches/{id}/price | PATCH | Đổi giá bán, giữ nguyên giá hóa đơn cũ |
| /batches/{id}/adjust | POST | Kiểm kê: quantity, expected_quantity, reason |
| /movements | GET | 1.000 biến động gần nhất |
| /alerts?days=90 | GET | Lô hết hạn/sắp hết hạn và tồn thấp |
| /invoices | GET/POST | Danh sách/bán hàng |
| /invoices/{id} | GET | Chi tiết hóa đơn |
| /invoices/{id}/cancel | POST | Hủy toàn bộ và hoàn kho |
| /reports?start=YYYY-MM-DD&end=YYYY-MM-DD | GET | Báo cáo doanh thu và tồn hiện tại |
| /ai/ask | POST | summary/expiry/procedure |
| /ai/logs | GET | 200 log gần nhất (quản lý) |

`GET /batches` hỗ trợ `q`, `category_id`, `expiry_before`, `available=true`.

Ví dụ body nhập lô (thay ID/ngày cho dữ liệu thật trong hệ thống):

```json
{
  "medicine_id": 1,
  "supplier_id": 1,
  "code": "LO-001",
  "received_date": "2026-09-12",
  "expiry_date": "2027-12-31",
  "quantity": 100,
  "purchase_price": "12000",
  "sale_price": "18000"
}
```

Ví dụ bán hàng:

```json
{
  "items": [{"batch_id": 1, "quantity": 2, "expected_sale_price": "18000"}],
  "customer": "Khách lẻ",
  "payment_method": "cash",
  "request_key": "THAY-BANG-UUID-RIENG-MOI-GIAO-DICH",
  "prescription_ref": ""
}
```

Khi retry cùng giao dịch, giữ nguyên toàn bộ body và request_key. Giao dịch mới phải có request_key mới. Nếu thuốc kê đơn, cần người lập có quyền và có prescription_ref.

Ví dụ AI:

```json
{"mode":"procedure","question":"Các bước kiểm kê tồn kho?","days":90}
```

```json
{"mode":"summary","medicine_id":1,"question":"","days":90}
```

```json
{"mode":"expiry","question":"","days":60}
```

Các mã phản hồi đáng chú ý: 401 cần đăng nhập; 403 sai quyền/origin/header; 409 xung đột tồn/giá/dữ liệu; 422 đầu vào hoặc nguồn không phù hợp; 429 giới hạn yêu cầu; 502 lỗi provider AI; 503 chưa cấu hình OpenAI.
