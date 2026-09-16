from datetime import date
from decimal import Decimal
from typing import Literal, Annotated
from pydantic import BaseModel, Field, ConfigDict

Name = Annotated[str, Field(min_length=1, max_length=160)]
Money = Annotated[Decimal, Field(ge=0, le=999999999, decimal_places=2)]

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

class Password(Input):
    old_password: str
    new_password: str = Field(min_length=10, max_length=200)

class UserIn(Input):
    username: str = Field(min_length=3, max_length=80, pattern=r'^[a-zA-Z0-9_.-]+$')
    name: Name
    password: str = Field(min_length=10, max_length=200)
    role: Literal['manager', 'pharmacist', 'cashier']

class UserState(Input):
    active: bool

class NameIn(Input):
    name: Name

class SupplierIn(NameIn):
    phone: str = Field(default='', max_length=30)
    address: str = Field(default='', max_length=300)
    active: bool = True

class MedicineIn(Input):
    code: str = Field(min_length=1, max_length=50)
    name: Name
    category_id: int = Field(gt=0)
    unit_id: int = Field(gt=0)
    min_stock: int = Field(default=10, ge=0, le=100000000)
    prescription_required: bool = False
    active: bool = True
    information: str = Field(default='', max_length=12000)
    source: str = Field(default='', max_length=500)

class BatchIn(Input):
    medicine_id: int = Field(gt=0)
    supplier_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=80)
    received_date: date
    expiry_date: date
    quantity: int = Field(gt=0, le=100000000)
    purchase_price: Money
    sale_price: Money

class BatchPrice(Input):
    sale_price: Money

class Adjustment(Input):
    quantity: int = Field(ge=0, le=100000000)
    expected_quantity: int = Field(ge=0)
    reason: str = Field(min_length=5, max_length=500)

class SaleItem(Input):
    expected_sale_price: Money
    batch_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100000000)

class Sale(Input):
    items: list[SaleItem] = Field(min_length=1, max_length=100)
    customer: str = Field(default='Khách lẻ', max_length=120)
    payment_method: Literal['cash', 'transfer'] = 'cash'
    request_key: str = Field(min_length=16, max_length=80)
    prescription_ref: str = Field(default='', max_length=200)

class Cancel(Input):
    reason: str = Field(min_length=5, max_length=500)

class ProcedureIn(Input):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=12000)

class AIRequest(Input):
    mode: Literal['summary', 'expiry', 'procedure', 'web']
    medicine_id: int | None = None
    question: str = Field(default='', max_length=2000)
    days: int = Field(default=90, ge=1, le=365)
