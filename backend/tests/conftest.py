import os
os.environ.setdefault('SECRET_KEY', 'test-secret-only-never-use-in-production-123456')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from datetime import timedelta
from app.db import Base, get_db
from app.main import app, _attempts
from app.models import User, Category, Unit, Supplier, Medicine, Batch
from app.auth import hash_password, token
from app.config import today

@pytest.fixture(scope='session')
def password_hash():
    return hash_password('TestingPass123!')

@pytest.fixture
def setup(password_hash):
    engine=create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    @event.listens_for(engine,'connect')
    def fk(conn, _): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    Session=sessionmaker(engine,expire_on_commit=False)
    with Session() as db:
        users=[User(username=role,name=role,role=role,password_hash=password_hash) for role in ['manager','pharmacist','cashier']]
        db.add_all(users)
        c=Category(name='Test');u=Unit(name='Hộp');s=Supplier(name='Test supplier')
        db.add_all([c,u,s]);db.flush()
        m=Medicine(code='M1',name='Thuốc kiểm thử',category_id=c.id,unit_id=u.id,min_stock=5, information='Thông tin nhận dạng đã kiểm tra.\nThông tin bảo quản đã kiểm tra.',source='Nguồn kiểm thử',approved=True)
        db.add(m);db.flush()
        b=Batch(medicine_id=m.id,supplier_id=s.id,code='B1',received_date=today()-timedelta(days=90),expiry_date=today()+timedelta(days=30),quantity=10,purchase_price=1000,sale_price=2000)
        db.add(b);db.commit()
        ids={'medicine':m.id,'batch':b.id,'supplier':s.id,'category':c.id,'unit':u.id}
        tokens={u.role:token(u) for u in users}
    def override():
        with Session() as db:
            try: yield db
            except Exception:
                db.rollback();raise
    app.dependency_overrides[get_db]=override
    _attempts.clear()
    with TestClient(app) as client:
        client.headers['X-Requested-With']='pharmacy'
        client.cookies.set('session',tokens['manager'])
        yield client,Session,ids,tokens
    app.dependency_overrides.clear()
    engine.dispose()
