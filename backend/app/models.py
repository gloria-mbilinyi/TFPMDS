"""Portable relational model. Currency = integer TZS; stock = integer kg."""
from datetime import datetime, timezone, date

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.now(timezone.utc)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Timestamped, Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role IN ('farmer','buyer','administrator','logistics','transporter')"),
        CheckConstraint("status IN ('pending','approved','rejected')"),
        CheckConstraint('farm_size_acres >= 0'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[str] = mapped_column(String(16))
    region: Mapped[str] = mapped_column(String(60))
    location: Mapped[str] = mapped_column(String(160), default='')
    farm_size_acres: Mapped[int] = mapped_column(default=0)
    crop_categories: Mapped[str] = mapped_column(String(250), default='')
    business_name: Mapped[str] = mapped_column(String(160), default='')
    verification_note: Mapped[str] = mapped_column(String(300), default='')


class RevokedToken(Base):
    __tablename__ = 'revoked_tokens'
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Produce(Timestamped, Base):
    __tablename__ = 'produce'
    __table_args__ = (CheckConstraint('available_kg >= 0'), CheckConstraint('price_tzs > 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    crop: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text, default='')
    available_kg: Mapped[int] = mapped_column(Integer)
    price_tzs: Mapped[int] = mapped_column(Integer)
    harvest_date: Mapped[date] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    farmer: Mapped[User] = relationship()


class PurchaseOrder(Timestamped, Base):
    __tablename__ = 'purchase_orders'
    __table_args__ = (UniqueConstraint('buyer_id', 'idempotency_key'), CheckConstraint('total_tzs > 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='pending_farmer_approval')
    total_tzs: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(80))
    fingerprint: Mapped[str] = mapped_column(String(64))
    delivery_address: Mapped[str] = mapped_column(String(250))
    note: Mapped[str] = mapped_column(String(300), default='')
    items: Mapped[list['OrderItem']] = relationship(cascade='all, delete-orphan')
    buyer: Mapped[User] = relationship(foreign_keys=[buyer_id])
    farmer: Mapped[User] = relationship(foreign_keys=[farmer_id])


class OrderItem(Base):
    __tablename__ = 'order_items'
    __table_args__ = (UniqueConstraint('order_id', 'produce_id'), CheckConstraint('quantity_kg > 0'), CheckConstraint('unit_price_tzs > 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('purchase_orders.id'), index=True)
    produce_id: Mapped[int] = mapped_column(ForeignKey('produce.id'))
    quantity_kg: Mapped[int] = mapped_column(Integer)
    unit_price_tzs: Mapped[int] = mapped_column(Integer)
    produce_name: Mapped[str] = mapped_column(String(100))


class Payment(Timestamped, Base):
    __tablename__ = 'payments'
    __table_args__ = (UniqueConstraint('buyer_id', 'idempotency_key'), CheckConstraint('amount_tzs > 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('purchase_orders.id'), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    provider: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(16))
    amount_tzs: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    reference: Mapped[str] = mapped_column(String(60), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(80))


class PaymentReceipt(Timestamped, Base):
    __tablename__ = 'payment_receipts'
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey('payments.id'), unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('purchase_orders.id'), unique=True)
    number: Mapped[str] = mapped_column(String(40), unique=True)
    amount_tzs: Mapped[int] = mapped_column(Integer)


class Shipment(Timestamped, Base):
    __tablename__ = 'shipments'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('purchase_orders.id'), unique=True)
    transporter_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='pending_arrangement')
    tracking_code: Mapped[str] = mapped_column(String(40), unique=True)
    order: Mapped[PurchaseOrder] = relationship()
    transporter: Mapped[User | None] = relationship()
    history: Mapped[list['TrackingEvent']] = relationship(order_by='TrackingEvent.id', cascade='all, delete-orphan')


class TrackingEvent(Timestamped, Base):
    __tablename__ = 'tracking_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey('shipments.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30))
    location: Mapped[str] = mapped_column(String(160))
    note: Mapped[str] = mapped_column(String(300), default='')


class Notification(Timestamped, Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(500))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_status: Mapped[str] = mapped_column(String(20), default='simulated')
    sms_reference: Mapped[str] = mapped_column(String(50))


class MarketPrice(Timestamped, Base):
    __tablename__ = 'market_prices'
    __table_args__ = (UniqueConstraint('crop', 'region'), CheckConstraint('price_tzs > 0'))
    id: Mapped[int] = mapped_column(primary_key=True)
    crop: Mapped[str] = mapped_column(String(50))
    region: Mapped[str] = mapped_column(String(60))
    price_tzs: Mapped[int] = mapped_column(Integer)
    observed_on: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(100), default='Illustrative demo data')
