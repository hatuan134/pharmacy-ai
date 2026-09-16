# Hướng dẫn chạy trên Windows với VS Code

## 1. Chuẩn bị

1. Giải nén `pharmacy-ai.zip` ra một thư mục dễ tìm, ví dụ `D:\Projects\pharmacy-ai`.
2. Cài Python 3.12, Node.js 22, Docker Desktop (nếu dùng cách A bên dưới). Chọn thêm Python vào PATH khi cài.
3. Mở Docker Desktop, đợi Docker Engine chạy.
4. Mở VS Code → **File → Open Folder** → chọn thư mục `pharmacy-ai` có `compose.yaml`, `backend` và `frontend`.
5. Mở **Terminal → New Terminal**. Hướng dẫn mặc định dùng **PowerShell**.
6. Kiểm tra:

```powershell
py --version
node --version
npm --version
docker --version
```

Nếu vừa cài phần mềm mà lệnh chưa nhận, đóng và mở lại VS Code.

## 2. Tạo cấu hình

Tại thư mục gốc `pharmacy-ai`:

```powershell
py scripts/setup.py
```

Lệnh tạo `.env` ở gốc cho PostgreSQL và `backend/.env` cho FastAPI, với mật khẩu database và khóa phiên ngẫu nhiên. Lệnh không ghi đè cấu hình cũ.

## 3. Khởi động PostgreSQL — chọn một cách

### Cách A: Dùng Docker Desktop

Trong terminal ở thư mục gốc:

```powershell
docker compose up -d db
docker compose ps
```

Lần đầu cần tải image PostgreSQL. Chạy lại `docker compose ps` đến khi dịch vụ `db` hiện `healthy`.
Nếu cần xem lỗi:

```powershell
docker compose logs db
```

Cổng mặc định: `5432`. Dữ liệu lưu trong volume `pharmacy_data`. Dừng bằng `docker compose stop`. Chạy lại bằng `docker compose up -d db`. **Không thêm `-v` vào lệnh xóa dịch vụ**, vì thao tác đó có thể xóa volume chứa dữ liệu.

### Cách B: Dùng PostgreSQL đã cài trên máy

Không cần chạy Docker. Mở pgAdmin, kết nối PostgreSQL, mở Query Tool ở database `postgres`.
Chạy hai câu lệnh riêng lẻ (không bọc trong một transaction):

```sql
CREATE USER pharmacy WITH PASSWORD 'THAY_BANG_MAT_KHAU_CUA_BAN';
```

```sql
CREATE DATABASE pharmacy OWNER pharmacy;
```

Mở `backend/.env`, sửa dòng sau cho khớp mật khẩu, cổng và database đã tạo:

```dotenv
DATABASE_URL=postgresql+psycopg://pharmacy:THAY_BANG_MAT_KHAU_CUA_BAN@localhost:5432/pharmacy
```

Nếu mật khẩu chứa ký tự như `@`, `:`, `/`, `#`, phải mã hóa URL phần mật khẩu. Với cách A, script thiết lập đã xử lý việc này.

## 4. Cài và chạy backend

Mở terminal mới bằng nút **+**. Bắt đầu tại thư mục gốc:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Chờ cài đặt xong. Tiếp theo:

```powershell
.\.venv\Scripts\python.exe -m app.init_db
```

Terminal hỏi mật khẩu quản lý. Gõ mật khẩu ít nhất 10 ký tự rồi Enter. Khi gõ, terminal có thể không hiện ký tự — đây là bình thường. Ghi nhớ mật khẩu này, tên đăng nhập là `admin`.

Chạy server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Đợi dòng `Application startup complete`. Giữ terminal này chạy.
Mở `http://localhost:8000/api/health`: kết quả bình thường là `{"status":"ok"}`.
Tài liệu API: `http://localhost:8000/docs`.

### Nếu dùng Git Bash trong VS Code

Các lệnh tương đương, từ thư mục gốc:

```bash
cd backend
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m app.init_db
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Không cần chạy `Activate.ps1` nên không bị vướng Execution Policy.

## 5. Cài và chạy frontend

Mở terminal mới bằng **+**, bắt đầu tại thư mục gốc:

```powershell
cd frontend
npm ci
npm run dev
```

Nếu PowerShell chặn file `npm.ps1`, dùng `npm.cmd ci` và `npm.cmd run dev`, hoặc chọn terminal Git Bash.

Mở `http://localhost:5173` trong Chrome/Edge.
Đăng nhập bằng `admin` và mật khẩu tự đặt ở bước 4.

**Không mở file `frontend/index.html` bằng Live Server hoặc bấm trực tiếp vào file.** Ứng dụng cần Vite để xử lý React và chuyển tiếp `/api` đến FastAPI.

## 6. Nhập dữ liệu ban đầu

CSDL mới chỉ có tài khoản quản lý. Các bảng trống là trạng thái bình thường.

1. **Thiết lập → Nhóm thuốc**: thêm nhóm.
2. **Thiết lập → Đơn vị tính**: thêm đơn vị, ví dụ Hộp. Chọn đơn vị tồn thống nhất cho từng mã thuốc.
3. **Nhà cung cấp → Thêm nhà cung cấp**: nhập tên và thông tin liên hệ.
4. **Danh mục thuốc → Thêm thuốc**: nhập mã, tên, nhóm, đơn vị, ngưỡng tồn. Đánh dấu kê đơn nếu cần.
5. **Lô nhập & tồn kho → Nhập lô mới**: chọn thuốc/nhà cung cấp, số lô, số lượng, ngày nhập, hạn dùng, giá nhập, giá bán.
6. Hạn dùng phải sau hôm nay và sau ngày nhập; ngày nhập không được ở tương lai.
7. Mở **Bán hàng tại quầy**: lô còn hạn và còn tồn sẽ xuất hiện.

### Dữ liệu luyện tập tùy chọn

Nếu muốn thử nhanh trước khi tự nhập, mở một terminal ở `backend`, chạy:

```powershell
.\.venv\Scripts\python.exe -m app.seed
```

Có ba sản phẩm thực hành và ba quy trình chưa duyệt. Đây là tên giả phục vụ học phần mềm, không có dữ liệu điều trị. Script chỉ thêm khi chưa có thuốc, không chạy tự động và không xóa dữ liệu có sẵn.

## 7. Thử luồng bán hàng, hủy và kiểm kê

1. Chọn thuốc trong **Bán hàng tại quầy**. Mỗi thẻ tương ứng một lô; lô gần hết hạn đứng trước.
2. Nhập số lượng, khách hàng và phương thức thanh toán.
3. Chỉ bấm **Xác nhận thanh toán** sau khi đã xác nhận nhận tiền. Với dữ liệu luyện tập, đây chỉ là giao dịch kiểm thử trong phần mềm.
4. Hóa đơn hiện lên → có thể in. Mở **Lô nhập & tồn kho** để xem tồn giảm đúng số lượng.
5. Mở **Hóa đơn → Chi tiết** để in lại.
6. Quản lý/dược sĩ có thể **Hủy đơn**, nhập lý do. Phần mềm hoàn lại hàng về đúng lô và loại hóa đơn khỏi doanh thu. Chỉ dùng khi hàng trả về đầy đủ.
7. Trong **Lô nhập & tồn kho → Kiểm kê**, nhập số lượng thực tế và lý do. Dùng cho kiểm kê, xử lý hàng hỏng/hết hạn sau khi có biên bản thực tế.
8. Mở **Lịch sử** để xem nhập, bán, hủy, điều chỉnh và đổi giá.

Nếu mạng mất sau khi bấm thanh toán, dùng **Thử lại thanh toán** để kiểm tra cùng mã giao dịch. Đừng mở giỏ mới trước khi kiểm tra hóa đơn vì giao dịch trước có thể đã thành công.

## 8. Cấu hình và sử dụng Gemini

1. Chuẩn bị Gemini API key cho tài khoản API của bạn. Không gửi key vào cuộc trò chuyện, ảnh chụp hoặc Git.
2. Mở `backend/.env` trong VS Code.
3. Sửa `GEMINI_API_KEY=` thành key của bạn. Giữ `GEMINI_MODEL=gemini-3.8-flash` hoặc đổi sang model Gemini tương thích với Interactions API và structured JSON mà tài khoản của bạn được phép dùng.
4. Lưu file.
5. Tại terminal backend, nhấn **Ctrl+C**, chạy lại lệnh uvicorn ở bước 4. Không chỉ tải lại trang web.
6. Trong **Danh mục thuốc**, nhập thông tin tham khảo, nguồn chính xác; lưu rồi bấm dấu tích **Duyệt thông tin** sau khi kiểm tra chuyên môn.
7. Trong **Quy trình nội bộ**, nhập nội dung, lưu và duyệt.
8. Mở **Trợ lý AI**: chọn hỏi đáp quy trình, tóm tắt thuốc hoặc báo cáo hạn dùng.
9. Quản lý có thể xem **Nhật ký AI**.

AI không tự duyệt nguồn, không ghi tồn kho, không kê đơn, không chỉ định liều. Cảnh báo hết hạn/tồn thấp được tính bằng code và vẫn hoạt động khi chưa có key.

## 9. Tạo tài khoản dược sĩ và thu ngân

Quản lý → **Nhân viên → Thêm nhân viên** → nhập tên đăng nhập, họ tên, mật khẩu và vai trò.

- Quản lý: quản trị tất cả chức năng và nhân viên.
- Dược sĩ: thuốc, lô, kiểm kê, bán hàng, hủy đơn, báo cáo, quy trình, AI; không quản trị nhân viên.
- Thu ngân: xem thuốc/lô/cảnh báo, bán thuốc không kê đơn, xem/in toàn bộ hóa đơn để tra cứu tại quầy, đổi mật khẩu; không được hủy hóa đơn, sửa danh mục hoặc tồn kho.

Đăng xuất rồi đăng nhập bằng từng vai trò để kiểm tra. Các API cũng kiểm tra quyền, không chỉ ẩn nút trên web.

## 10. Chạy lại vào lần sau

Không cần cài lại hoặc chạy `init_db` mỗi lần.

1. Mở Docker Desktop, từ thư mục gốc chạy `docker compose up -d db` (nếu dùng Docker).
2. Terminal ở `backend`: chạy lệnh uvicorn.
3. Terminal ở `frontend`: chạy `npm run dev`.
4. Mở `http://localhost:5173`.

## 11. Lỗi thường gặp

| Dấu hiệu | Cách kiểm tra / xử lý |
|---|---|
| `py` hoặc `node` không được nhận diện | Cài đúng công cụ, mở lại VS Code để cập nhật PATH |
| Không có Python 3.12 | Cài 3.12 hoặc dùng Python 3.11+ và sửa lệnh tạo môi trường phù hợp |
| `docker` không kết nối được daemon | Mở Docker Desktop, chờ Engine chạy |
| Cổng 5432 đã được sử dụng | Chọn PostgreSQL có sẵn, hoặc sửa cổng ngoài trong compose thành 5433 và URL backend thành 5433 |
| `password authentication failed` | Kiểm tra username/password trong URL khớp database. Đổi `.env` không tự đổi mật khẩu của volume PostgreSQL đã tồn tại |
| `connection refused` / backend không lên | Kiểm tra database `healthy`, cổng và URL đúng; xem terminal backend |
| `relation ... does not exist` | Chạy `python -m app.init_db` bằng đúng môi trường backend và đúng database |
| `SECRET_KEY` thiếu | Chạy `py scripts/setup.py` từ gốc; kiểm tra backend chạy tại thư mục `backend` |
| Trang trắng hoặc mã JSX không chạy | Dùng `npm run dev`, mở cổng 5173; không dùng Live Server. Thử `npm run build` để thấy lỗi cụ thể |
| `EADDRINUSE` ở 8000 hoặc 5173 | Dừng tiến trình cũ đang chiếm cổng; Vite dùng `strictPort` để không âm thầm đổi cổng |
| Đăng nhập xong vẫn quay về đăng nhập | Dùng nhất quán `localhost:5173`, không trộn hostname và không đặt `COOKIE_SECURE=true` khi chạy HTTP local |
| AI báo thiếu API key | Điền `backend/.env`, khởi động lại backend |
| AI báo key không hợp lệ/hết hạn mức | Kiểm tra tài khoản API, hạn mức và quyền model; key chỉ dùng trên backend |
| AI không có dữ liệu | Duyệt thông tin thuốc có nguồn / quy trình trước; báo cáo hạn dùng cần có lô còn tồn trong khoảng cảnh báo |
| Không thấy thuốc ở quầy | Thuốc phải đang kinh doanh; lô phải còn tồn và hạn dùng sau hôm nay |
| Không bán được thuốc kê đơn | Dược sĩ/quản lý phải kiểm tra đơn và nhập mã tham chiếu; thu ngân không được bán loại này |
| Xóa thuốc hoặc nhà cung cấp bị chặn | Bản ghi đã được dùng ở lô/hóa đơn. Dùng trạng thái ngừng hoạt động để giữ lịch sử |
| Kiểm kê báo tồn đã thay đổi | Có giao dịch khác vừa thay đổi lô. Đóng form, tải lại và đối chiếu lại số lượng |

## 12. Linux/macOS

Từ thư mục gốc, dùng `python3 scripts/setup.py` và `docker compose up -d db`.
Trong `backend`, tạo venv và gọi Python của venv:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m app.init_db
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Frontend dùng `npm ci` và `npm run dev` như Windows.
