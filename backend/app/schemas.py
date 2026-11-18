from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PositiveInt = Annotated[int, Field(strict=True, gt=0, le=1_000_000_000)]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
Phone = Annotated[str, Field(pattern=r'^\+255[67]\d{8}$')]
Name = Annotated[str, Field(min_length=2, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Profile(Input):
    name: Name
    phone: Phone
    region: Annotated[str, Field(min_length=2, max_length=60)]
    location: Annotated[str, Field(max_length=160)] = ''
    farm_size_acres: NonNegativeInt = 0
    crop_categories: Annotated[str, Field(max_length=250)] = ''
    business_name: Annotated[str, Field(max_length=160)] = ''


class Register(Profile):
    email: EmailStr
    password: Annotated[str, Field(min_length=10, max_length=128)]
    role: Literal['farmer', 'buyer']

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class Login(Input):
    email: EmailStr
    password: Annotated[str, Field(max_length=128)]


class UserOut(Profile):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    status: str
    active: bool
    verification_note: str
    created_at: datetime


class Approval(Input):
    status: Literal['approved', 'rejected']
    note: Annotated[str, Field(min_length=3, max_length=300)]


class ActiveChange(Input):
    active: bool


class StaffCreate(Profile):
    email: EmailStr
    password: Annotated[str, Field(min_length=10, max_length=128)]
    role: Literal['logistics', 'transporter']


class ProduceInput(Input):
    name: Name
    crop: Annotated[str, Field(min_length=2, max_length=50)]
    description: Annotated[str, Field(max_length=2000)] = ''
    available_kg: NonNegativeInt
    price_tzs: PositiveInt
    harvest_date: date


class ProduceEdit(ProduceInput):
    pass


class OrderLine(Input):
    produce_id: PositiveInt
    quantity_kg: PositiveInt


class OrderCreate(Input):
    items: Annotated[list[OrderLine], Field(min_length=1, max_length=30)]
    delivery_address: Annotated[str, Field(min_length=5, max_length=250)]


class Decision(Input):
    action: Literal['accept', 'reject', 'cancel', 'complete']
    note: Annotated[str, Field(max_length=300)] = ''


class PaymentCreate(Input):
    order_id: PositiveInt
    provider: Literal['mpesa', 'airtel_money', 'tigo_pesa']
    phone: Phone


class PaymentOutcome(Input):
    outcome: Literal['successful', 'failed', 'cancelled']


class Callback(PaymentOutcome):
    reference: Annotated[str, Field(min_length=5, max_length=60)]


class Assign(Input):
    transporter_id: PositiveInt


class ShipmentUpdate(Input):
    status: Literal['awaiting_transporter', 'assignment_failed', 'ready_for_pickup', 'picked_up', 'in_transit', 'delivered', 'delivery_failed', 'return_requested', 'returned']
    location: Annotated[str, Field(min_length=2, max_length=160)]
    note: Annotated[str, Field(max_length=300)] = ''


class MarketPriceInput(Input):
    crop: Annotated[str, Field(min_length=2, max_length=50)]
    region: Annotated[str, Field(min_length=2, max_length=60)]
    price_tzs: PositiveInt
    observed_on: date
    source: Annotated[str, Field(min_length=3, max_length=100)] = 'Illustrative demo data'
