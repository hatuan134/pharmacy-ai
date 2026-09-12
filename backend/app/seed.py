"""Optional explicitly requested training data; never runs automatically."""
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .config import today
from .services import movement

def main():
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.role=='manager'))
        if not user: raise SystemExit('Chạy python -m app.init_db trước.')
        if db.scalar(select(Medicine.id).limit(1)): raise SystemExit('Đã có thuốc. Không thêm dữ liệu luyện tập để tránh trộn dữ liệu.')
        category = Category(name='Danh mục thực hành'); unit = Unit(name='Hộp')
        supplier = Supplier(name='Nhà cung cấp thực hành', address='Dữ liệu phục vụ học tập')
        db.add_all([category,unit,supplier]); db.flush()
        for index,(name,days,qty,price) in enumerate([('Sản phẩm thực hành A',30,40,25000),('Sản phẩm thực hành B',180,5,45000),('Sản phẩm thực hành C',300,100,18000)],1):
            medicine = Medicine(code=f'TH{index:03}', name=name, category_id=category.id, unit_id=unit.id, min_stock=10, information='Mặt hàng phục vụ thực hành thao tác phần mềm.\nKhông phải thông tin dược phẩm dùng để tư vấn.', source='Bộ dữ liệu luyện tập của dự án', approved=True, approved_by=user.id)
            db.add(medicine); db.flush()
            batch = Batch(medicine_id=medicine.id,supplier_id=supplier.id,code=f'LO-TH-{index}', received_date=today(),expiry_date=today()+timedelta(days=days),quantity=qty,purchase_price=Decimal(price)*Decimal("0.7"),sale_price=price)
            db.add(batch); db.flush(); movement(db,batch,user,qty,'receipt','Dữ liệu luyện tập')
        for title,content in [
            ('Nhập lô thuốc','1. Đối chiếu nhà cung cấp, mã thuốc và chứng từ.\n2. Kiểm tra số lô, hạn dùng và số lượng thực nhận.\n3. Nhập ngày nhập, hạn dùng, giá và số lượng.\n4. Lưu lô và kiểm tra lịch sử nhập kho.'),
            ('Kiểm kê tồn kho','1. Tạm dừng thao tác liên quan đến lô đang kiểm kê.\n2. Đếm số lượng thực tế theo lô.\n3. Đối chiếu số lượng trên phần mềm.\n4. Nhập số lượng thực tế và lý do chênh lệch.\n5. Lưu điều chỉnh, kiểm tra lịch sử tồn kho.'),
            ('Xử lý lô hết hạn','1. Ngừng bán và cách ly lô hết hạn.\n2. Dược sĩ đối chiếu số lượng, lập biên bản.\n3. Quản lý xử lý đổi trả hoặc tiêu hủy theo quy trình đã phê duyệt.\n4. Sau khi xử lý thực tế, điều chỉnh tồn kho và ghi rõ số biên bản.')]:
            db.add(Procedure(title=title,content=content,approved=False))
        db.commit()
        print('Đã thêm dữ liệu luyện tập. Dược sĩ cần kiểm tra và duyệt quy trình trước khi AI sử dụng.')
if __name__ == '__main__': main()
