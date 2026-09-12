from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Text, ForeignKey, Numeric, CheckConstraint, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(default=True)
    token_version: Mapped[int] = mapped_column(default=0)
    __table_args__ = (CheckConstraint("role IN ('manager','pharmacist','cashier')"),)

class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

class Unit(Base):
    __tablename__ = 'units'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)

class Supplier(Base):
    __tablename__ = 'suppliers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    phone: Mapped[str] = mapped_column(String(30), default='')
    address: Mapped[str] = mapped_column(String(300), default='')
    active: Mapped[bool] = mapped_column(default=True)

class Medicine(Base):
    __tablename__ = 'medicines'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    unit_id: Mapped[int] = mapped_column(ForeignKey('units.id'))
    min_stock: Mapped[int] = mapped_column(default=10)
    prescription_required: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)
    information: Mapped[str] = mapped_column(Text, default='')
    source: Mapped[str] = mapped_column(String(500), default='')
    approved: Mapped[bool] = mapped_column(default=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    __table_args__ = (CheckConstraint('min_stock >= 0'),)

class Batch(Base):
    __tablename__ = 'batches'
    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey('medicines.id'), index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey('suppliers.id'))
    code: Mapped[str] = mapped_column(String(80))
    received_date: Mapped[date]
    expiry_date: Mapped[date] = mapped_column(index=True)
    quantity: Mapped[int]
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    __table_args__ = (UniqueConstraint('medicine_id', 'code'), CheckConstraint('quantity >= 0'), CheckConstraint('purchase_price >= 0'), CheckConstraint('sale_price >= 0'), CheckConstraint('expiry_date > received_date'))

class Invoice(Base):
    __tablename__ = 'invoices'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    customer: Mapped[str] = mapped_column(String(120), default='Khách lẻ')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    total: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    status: Mapped[str] = mapped_column(String(20), default='paid')
    payment_method: Mapped[str] = mapped_column(String(20), default='cash')
    request_key: Mapped[str] = mapped_column(String(80), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    prescription_ref: Mapped[str] = mapped_column(String(200), default='')
    cancel_reason: Mapped[str] = mapped_column(String(500), default='')
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    __table_args__ = (CheckConstraint("status IN ('paid','cancelled')"), CheckConstraint('total >= 0'))

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('batches.id'))
    medicine_name: Mapped[str] = mapped_column(String(180))
    unit_name: Mapped[str] = mapped_column(String(60))
    quantity: Mapped[int]
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    __table_args__ = (CheckConstraint('quantity > 0'), UniqueConstraint('invoice_id', 'batch_id'))

class Movement(Base):
    __tablename__ = 'inventory_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('batches.id'), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey('invoices.id'), nullable=True)
    delta: Mapped[int]
    balance: Mapped[int]
    kind: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(String(500), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Procedure(Base):
    __tablename__ = 'procedures'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(default=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)

class AILog(Base):
    __tablename__ = 'ai_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    mode: Mapped[str] = mapped_column(String(30))
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    sources: Mapped[str] = mapped_column(Text, default='[]')
    status: Mapped[str] = mapped_column(String(30))
    warning: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
