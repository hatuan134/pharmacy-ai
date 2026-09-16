from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict, deque
from decimal import Decimal
import time as clock
from threading import Lock
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .config import settings, today
from .db import get_db
from .models import *
from .schemas import *
from .auth import current_user, staff, ai_user, manager, verify_password, hash_password, token
from .services import require, row, movement, batch_rows, alerts, create_sale, cancel_sale, invoice_detail
from . import ai

def documented_header(x_requested_with: str = Header(default='pharmacy')):
    # Expose this header in Swagger; actual validation is performed by middleware.
    return x_requested_with

app = FastAPI(title='An Tâm · Quản lý nhà thuốc', version='1.0.0', dependencies=[Depends(documented_header)])
origins = [x.strip() for x in settings.cors_origins.split(',')]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['GET','POST','PUT','PATCH','DELETE'], allow_headers=['Content-Type','X-Requested-With'])

@app.middleware('http')
async def csrf(request: Request, call_next):
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        origin = request.headers.get('origin')
        if (origin and origin not in origins) or request.headers.get('x-requested-with') != 'pharmacy':
            return JSONResponse(status_code=403, content={'detail':'Yêu cầu không hợp lệ. Vui lòng thao tác từ ứng dụng.'})
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={'detail':'Dữ liệu trùng hoặc đang được sử dụng. Kiểm tra mã, tên và các liên kết.'})

@app.get('/api/health')
def health(db=Depends(get_db)):
    db.execute(select(1))
    return {'status':'ok'}

_attempts = defaultdict(deque)
_attempt_lock = Lock()
def rate_limit(key, limit, seconds):
    with _attempt_lock:
        now = clock.monotonic()
        # Bound memory for local single-worker deployment.
        if len(_attempts) > 5000:
            for old in list(_attempts):
                if not _attempts[old] or _attempts[old][-1] < now-3600:
                    del _attempts[old]
        queue = _attempts[key]
        while queue and queue[0] < now-seconds:
            queue.popleft()
        if len(queue) >= limit:
            raise HTTPException(429, 'Bạn thao tác quá nhanh. Vui lòng thử lại sau.')
        queue.append(now)

@app.post('/api/auth/login')
def login(data: Login, response: Response, request: Request, db=Depends(get_db)):
    rate_limit('login:'+(request.client.host if request.client else 'local'), 15, 300)
    user = db.scalar(select(User).where(User.username == data.username))
    # Constant-cost verification even for unknown usernames.
    dummy = '0'*32 + ':' + '0'*64
    valid = verify_password(data.password, user.password_hash if user else dummy)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    response.set_cookie('session', token(user), httponly=True, samesite='strict', secure=settings.cookie_secure, max_age=28800)
    return row(user)

@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return row(user)

@app.post('/api/auth/logout')
def logout(response: Response, user=Depends(current_user), db=Depends(get_db)):
    user.token_version += 1
    db.commit()
    response.delete_cookie('session')
    return {'message':'Đã đăng xuất.'}

@app.post('/api/auth/password')
def password(data: Password, response: Response, user=Depends(current_user), db=Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, 'Mật khẩu cũ không đúng.')
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1
    db.commit()
    response.set_cookie('session', token(user), httponly=True, samesite='strict', secure=settings.cookie_secure, max_age=28800)
    return {'message':'Đã đổi mật khẩu.'}

@app.get('/api/users')
def users(user=Depends(manager), db=Depends(get_db)):
    return [row(u) for u in db.scalars(select(User).order_by(User.id))]

@app.post('/api/users')
def user_create(data: UserIn, user=Depends(manager), db=Depends(get_db)):
    item = User(**data.model_dump(exclude={'password'}), password_hash=hash_password(data.password))
    db.add(item); db.commit()
    return row(item)

@app.patch('/api/users/{ident}')
def user_state(ident: int, data: UserState, user=Depends(manager), db=Depends(get_db)):
    item = require(db, User, ident)
    if item.id == user.id:
        raise HTTPException(409, 'Không thể khóa tài khoản đang đăng nhập.')
    item.active = data.active; item.token_version += 1
    db.commit()
    return row(item)

def catalog(path, model, schema, permission=staff):
    def listing(user=Depends(current_user), db=Depends(get_db)):
        return [row(x) for x in db.scalars(select(model).order_by(model.id.desc()))]
    def validate(db, values, existing=None):
        if model is Medicine:
            require(db, Category, values['category_id']); require(db, Unit, values['unit_id'])
            if existing and existing.unit_id != values['unit_id'] and db.scalar(select(Batch.id).where(Batch.medicine_id == existing.id).limit(1)):
                raise HTTPException(409, 'Thuốc đã có lô: không thể đổi đơn vị tính. Hãy tạo mã thuốc mới.')
    def create(data: schema, user=Depends(permission), db=Depends(get_db)):
        values = data.model_dump(); validate(db, values)
        obj = model(**values); db.add(obj); db.commit()
        return row(obj)
    def update(ident: int, data: schema, user=Depends(permission), db=Depends(get_db)):
        obj = require(db, model, ident)
        values = data.model_dump(); validate(db, values, obj)
        if model in (Medicine, Procedure):
            obj.approved = False; obj.approved_by = None
        for key, value in values.items():
            setattr(obj, key, value)
        db.commit()
        return row(obj)
    def delete(ident: int, user=Depends(permission), db=Depends(get_db)):
        obj = require(db, model, ident)
        db.delete(obj); db.commit()
        return {'message':'Đã xóa.'}
    app.add_api_route('/api/'+path, listing, methods=['GET'], name=path+'_list')
    app.add_api_route('/api/'+path, create, methods=['POST'], name=path+'_create')
    app.add_api_route('/api/'+path+'/{ident}', update, methods=['PUT'], name=path+'_update')
    app.add_api_route('/api/'+path+'/{ident}', delete, methods=['DELETE'], name=path+'_delete')

catalog('categories', Category, NameIn)
catalog('units', Unit, NameIn)
catalog('suppliers', Supplier, SupplierIn)
catalog('medicines', Medicine, MedicineIn)
catalog('procedures', Procedure, ProcedureIn)

@app.post('/api/{kind}/{ident}/approve')
def approve(kind: Literal['medicines','procedures'], ident: int, user=Depends(staff), db=Depends(get_db)):
    obj = require(db, Medicine if kind == 'medicines' else Procedure, ident)
    if kind == 'medicines' and (not obj.information or not obj.source):
        raise HTTPException(422, 'Cần nhập thông tin thuốc và nguồn trước khi duyệt.')
    obj.approved = True; obj.approved_by = user.id; db.commit()
    return row(obj)

@app.get('/api/batches')
def batches(q: str='', category_id: int | None=None, expiry_before: date | None=None, available: bool=False, user=Depends(current_user), db=Depends(get_db)):
    return batch_rows(db, q, category_id, expiry_before, available)

@app.post('/api/batches')
def batch_create(data: BatchIn, user=Depends(staff), db=Depends(get_db)):
    medicine = require(db, Medicine, data.medicine_id)
    supplier = require(db, Supplier, data.supplier_id)
    if not medicine.active or not supplier.active:
        raise HTTPException(422, 'Thuốc hoặc nhà cung cấp đã ngừng hoạt động.')
    if data.expiry_date <= today() or data.expiry_date <= data.received_date or data.received_date > today():
        raise HTTPException(422, 'Ngày nhập không được ở tương lai; hạn dùng phải sau ngày nhập và sau hôm nay.')
    batch = Batch(**data.model_dump()); db.add(batch); db.flush()
    movement(db, batch, user, batch.quantity, 'receipt', 'Nhập lô mới')
    db.commit()
    return row(batch)

@app.patch('/api/batches/{ident}/price')
def batch_price(ident: int, data: BatchPrice, user=Depends(staff), db=Depends(get_db)):
    batch = db.scalar(select(Batch).where(Batch.id == ident).with_for_update())
    if not batch: raise HTTPException(404, 'Không tìm thấy lô.')
    old_price = batch.sale_price
    batch.sale_price = data.sale_price
    movement(db, batch, user, 0, 'price', f'Giá bán: {old_price} → {data.sale_price}')
    db.commit(); return row(batch)

@app.post('/api/batches/{ident}/adjust')
def adjust(ident: int, data: Adjustment, user=Depends(staff), db=Depends(get_db)):
    batch = db.scalar(select(Batch).where(Batch.id == ident).with_for_update())
    if not batch: raise HTTPException(404, 'Không tìm thấy lô.')
    if batch.quantity != data.expected_quantity:
        raise HTTPException(409, 'Tồn kho đã thay đổi. Tải lại rồi kiểm kê lại.')
    delta = data.quantity - batch.quantity
    batch.quantity = data.quantity
    movement(db, batch, user, delta, 'adjustment', data.reason)
    db.commit(); return row(batch)

@app.get('/api/movements')
def movements(user=Depends(staff), db=Depends(get_db)):
    return [row(x) for x in db.scalars(select(Movement).order_by(Movement.id.desc()).limit(1000))]

@app.get('/api/alerts')
def alert_list(days: int=Query(90, ge=1, le=365), user=Depends(current_user), db=Depends(get_db)):
    return alerts(db, days)

@app.post('/api/invoices')
def sale(data: Sale, user=Depends(current_user), db=Depends(get_db)):
    return create_sale(db, data, user)

@app.get('/api/invoices')
def invoices(user=Depends(current_user), db=Depends(get_db)):
    # Mọi tài khoản đã đăng nhập đều được tra cứu danh sách hóa đơn.
    # Quyền hủy hóa đơn vẫn được giới hạn cho quản lý/dược sĩ ở endpoint riêng.
    stmt = select(Invoice).order_by(Invoice.id.desc()).limit(1000)
    return [row(i) for i in db.scalars(stmt)]

@app.get('/api/invoices/{ident}')
def invoice(ident: int, user=Depends(current_user), db=Depends(get_db)):
    # Thu ngân cần xem/in được cả hóa đơn do nhân viên khác lập để tra cứu tại quầy.
    item = require(db, Invoice, ident)
    return invoice_detail(db, item)

@app.post('/api/invoices/{ident}/cancel')
def cancel(ident: int, data: Cancel, user=Depends(staff), db=Depends(get_db)):
    return cancel_sale(db, ident, data.reason, user)

@app.get('/api/reports')
def reports(start: date | None=None, end: date | None=None, user=Depends(staff), db=Depends(get_db)):
    start = start or today().replace(day=1); end = end or today()
    if start > end: raise HTTPException(422, 'Ngày bắt đầu phải trước ngày kết thúc.')
    zone = ZoneInfo('Asia/Ho_Chi_Minh')
    lower = datetime.combine(start, time.min, zone).astimezone(timezone.utc)
    upper = datetime.combine(end+timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    rows = list(db.scalars(select(Invoice).where(Invoice.status=='paid', Invoice.created_at >= lower, Invoice.created_at < upper)))
    series = defaultdict(Decimal)
    for inv in rows:
        timestamp = inv.created_at.replace(tzinfo=timezone.utc) if inv.created_at.tzinfo is None else inv.created_at
        series[timestamp.astimezone(zone).date().isoformat()] += inv.total
    stock = batch_rows(db)
    return {'start': start, 'end': end, 'revenue':sum((i.total for i in rows), Decimal(0)), 'invoice_count':len(rows), 'stock_value':sum((b['quantity']*b['purchase_price'] for b in stock), Decimal(0)), 'total_units':sum(b['quantity'] for b in stock), 'medicine_count':len(list(db.scalars(select(Medicine).where(Medicine.active.is_(True))))), 'series':[{'date':k,'revenue':v} for k,v in sorted(series.items())], 'alerts':alerts(db)}

@app.post('/api/ai/ask')
def ask(data: AIRequest, user=Depends(ai_user), db=Depends(get_db)):
    rate_limit('ai:'+str(user.id), 10, 60)
    return ai.answer(db, data, user)

@app.get('/api/ai/logs')
def ai_logs(user=Depends(manager), db=Depends(get_db)):
    return [row(x) for x in db.scalars(select(AILog).order_by(AILog.id.desc()).limit(200))]
