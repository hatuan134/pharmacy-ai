"""PostgreSQL locking test. Uses an isolated, randomly named schema.
Set TEST_POSTGRES_URL to a dedicated test database; never production.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from datetime import timedelta
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import User, Medicine, Category, Unit, Supplier, Batch, Invoice
from app.schemas import Sale
from app.auth import hash_password
from app.services import create_sale
from app.config import today

@pytest.mark.postgres
def test_concurrent_sales_do_not_oversell():
    url=os.getenv('TEST_POSTGRES_URL')
    if not url: pytest.skip('Set TEST_POSTGRES_URL to run real PostgreSQL concurrency verification.')
    schema='pharmacy_test_'+uuid4().hex
    admin=create_engine(url)
    with admin.begin() as connection: connection.execute(text(f'CREATE SCHEMA {schema}'))
    engine=create_engine(url,connect_args={'options':f'-csearch_path={schema}'})
    try:
        Base.metadata.create_all(engine)
        S=sessionmaker(engine,expire_on_commit=False)
        with S() as db:
            users=[User(username=f'user{i}',name=f'User {i}',role='cashier',password_hash=hash_password('TestPassword123')) for i in range(2)]
            c=Category(name='Test');u=Unit(name='Box');s=Supplier(name='Supplier')
            db.add_all([*users,c,u,s]);db.flush()
            m=Medicine(code='M',name='Medicine',category_id=c.id,unit_id=u.id)
            db.add(m);db.flush()
            b=Batch(medicine_id=m.id,supplier_id=s.id,code='LOT',received_date=today(),expiry_date=today()+timedelta(days=30),quantity=10,purchase_price=1000,sale_price=2000)
            db.add(b);db.commit()
            user_ids=[u.id for u in users];batch_id=b.id
        from threading import Barrier
        barrier=Barrier(2)
        def sell(user_id):
            with S() as db:
                user=db.get(User,user_id)
                request=Sale(items=[{'batch_id':batch_id,'quantity':7,'expected_sale_price':2000}],request_key=str(uuid4()))
                barrier.wait(timeout=10)
                try:
                    create_sale(db,request,user)
                    return 200
                except HTTPException as e:
                    db.rollback();return e.status_code
        with ThreadPoolExecutor(2) as pool: results=list(pool.map(sell,user_ids))
        assert sorted(results)==[200,409]
        with S() as db:
            assert db.get(Batch,batch_id).quantity==3
            assert db.scalar(select(func.count(Invoice.id)))==1
    finally:
        engine.dispose()
        with admin.begin() as connection: connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()
