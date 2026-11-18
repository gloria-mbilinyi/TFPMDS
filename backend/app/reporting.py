from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import MarketPrice, Notification, OrderItem, Payment, Produce, PurchaseOrder, Shipment, User
from .schemas import MarketPriceInput
from .security import authorize, current_user, find_or_404

router = APIRouter(prefix='/api', tags=['administration and reporting'])


@router.get('/reports/summary')
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    def count(model, *conditions):
        return db.scalar(select(func.count()).select_from(model).where(*conditions))
    by_crop = db.execute(select(OrderItem.produce_name, func.sum(OrderItem.quantity_kg),
                                func.sum(OrderItem.quantity_kg * OrderItem.unit_price_tzs))
                         .join(PurchaseOrder, OrderItem.order_id == PurchaseOrder.id)
                         .join(Payment, Payment.order_id == PurchaseOrder.id)
                         .where(Payment.status == 'successful').group_by(OrderItem.produce_name)).all()
    regions = db.execute(select(User.region, func.sum(Payment.amount_tzs)).join(PurchaseOrder, PurchaseOrder.farmer_id == User.id)
                         .join(Payment, Payment.order_id == PurchaseOrder.id).where(Payment.status == 'successful').group_by(User.region)).all()
    states = db.execute(select(PurchaseOrder.status, func.count()).group_by(PurchaseOrder.status)).all()
    return {
        'users': count(User), 'farmers': count(User, User.role == 'farmer'), 'buyers': count(User, User.role == 'buyer'),
        'pending_approvals': count(User, User.status == 'pending'), 'active_listings': count(Produce, Produce.active.is_(True)),
        'orders': count(PurchaseOrder), 'completed_orders': count(PurchaseOrder, PurchaseOrder.status == 'completed'),
        'successful_payments': count(Payment, Payment.status == 'successful'),
        'gross_sales_tzs': db.scalar(select(func.coalesce(func.sum(Payment.amount_tzs), 0)).where(Payment.status == 'successful')),
        'shipments': count(Shipment), 'delivered_shipments': count(Shipment, Shipment.status == 'delivered'),
        'sms_simulated': count(Notification), 'currency': 'TZS', 'mode': 'simulation',
        'sales_by_produce': [{'produce': name, 'quantity_kg': kg, 'sales_tzs': sales} for name, kg, sales in by_crop],
        'sales_by_region': [{'region': region, 'sales_tzs': sales} for region, sales in regions],
        'orders_by_status': [{'status': status, 'count': total} for status, total in states],
        'definition': 'Gross successful simulated payment value; no real money, fees or refunds. Returned shipments remain included until a future refund workflow.',
    }


@router.post('/admin/market-prices', status_code=201)
def save_market_price(data: MarketPriceInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    record = db.scalar(select(MarketPrice).where(MarketPrice.crop == data.crop, MarketPrice.region == data.region))
    if record:
        for key, value in data.model_dump().items():
            setattr(record, key, value)
    else:
        record = MarketPrice(**data.model_dump()); db.add(record)
    db.flush()
    return record


@router.delete('/admin/market-prices/{price_id}')
def delete_price(price_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    db.delete(find_or_404(db, MarketPrice, price_id))
    return {'message': 'Market price removed.'}
