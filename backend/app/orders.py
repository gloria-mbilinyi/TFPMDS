import hashlib
import json

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import OrderItem, Produce, PurchaseOrder, User
from .notifications import notify
from .schemas import Decision, OrderCreate
from .security import authorize, current_user, find_or_404
from .views import order_view

router = APIRouter(prefix='/api/orders', tags=['purchase orders'])


def accessible(order, user):
    require(user.role in {'administrator', 'logistics'} or user.id in {order.buyer_id, order.farmer_id},
            403, 'not_order_party', 'This order belongs to another account.')


def transition(db, order, expected, new_status):
    result = db.execute(update(PurchaseOrder).where(PurchaseOrder.id == order.id, PurchaseOrder.status.in_(expected)).values(status=new_status))
    require(result.rowcount == 1, 409, 'order_changed', 'Order state changed. Refresh before retrying.')
    db.refresh(order)


@router.post('', status_code=201)
def create(data: OrderCreate, idempotency_key: str = Header(min_length=8, max_length=80),
           user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'buyer')
    ids = [item.produce_id for item in data.items]
    require(len(ids) == len(set(ids)), 422, 'duplicate_item', 'Combine repeated produce into one order line.')
    body = data.model_dump(); body['items'] = sorted(body['items'], key=lambda item: item['produce_id'])
    fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    existing = db.scalar(select(PurchaseOrder).where(PurchaseOrder.buyer_id == user.id, PurchaseOrder.idempotency_key == idempotency_key))
    if existing:
        require(existing.fingerprint == fingerprint, 409, 'idempotency_mismatch', 'This key was used for a different order.')
        return order_view(existing)
    records = [find_or_404(db, Produce, item.produce_id) for item in data.items]
    farmer_ids = {p.farmer_id for p in records}
    require(len(farmer_ids) == 1, 422, 'multiple_farmers', 'Place separate orders for different farmers.')
    farmer = find_or_404(db, User, next(iter(farmer_ids)))
    require(farmer.active and farmer.status == 'approved', 409, 'farmer_unavailable', 'This farmer is not currently approved.')
    total = sum(item.quantity_kg * record.price_tzs for item, record in zip(data.items, records))
    require(total <= 9_000_000_000_000_000, 422, 'amount_limit', 'Order value exceeds the supported amount.')
    order = PurchaseOrder(buyer_id=user.id, farmer_id=farmer.id, total_tzs=total,
                          delivery_address=data.delivery_address, idempotency_key=idempotency_key, fingerprint=fingerprint)
    db.add(order); db.flush()
    for item, record in zip(data.items, records):
        result = db.execute(update(Produce).where(Produce.id == record.id, Produce.active.is_(True),
                                                  Produce.available_kg >= item.quantity_kg).values(available_kg=Produce.available_kg - item.quantity_kg))
        require(result.rowcount == 1, 409, 'insufficient_stock', f'{record.name} has insufficient available stock.')
        order.items.append(OrderItem(produce_id=record.id, quantity_kg=item.quantity_kg,
                                     unit_price_tzs=record.price_tzs, produce_name=record.name))
    notify(db, farmer, 'order', f'Order #{order.id} needs your approval. Stock has been reserved.')
    notify(db, user, 'order', f'Order #{order.id} submitted and awaiting farmer approval.')
    db.flush()
    return order_view(order)


@router.get('')
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    if user.role not in {'administrator', 'logistics'}:
        query = query.where((PurchaseOrder.buyer_id == user.id) | (PurchaseOrder.farmer_id == user.id))
    return [order_view(o) for o in db.scalars(query)]


@router.get('/{order_id}')
def detail(order_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    order = find_or_404(db, PurchaseOrder, order_id); accessible(order, user)
    return order_view(order)


@router.post('/{order_id}/decision')
def decide(order_id: int, data: Decision, user: User = Depends(current_user), db: Session = Depends(get_db)):
    order = find_or_404(db, PurchaseOrder, order_id)
    if data.action in {'accept', 'reject'}:
        authorize(user, 'farmer')
        require(order.farmer_id == user.id, 403, 'not_order_farmer', 'Only the responsible farmer may decide this order.')
        transition(db, order, {'pending_farmer_approval'}, 'accepted' if data.action == 'accept' else 'rejected')
    elif data.action == 'cancel':
        require(order.buyer_id == user.id, 403, 'not_order_buyer', 'Only the buyer may cancel this order.')
        transition(db, order, {'pending_farmer_approval', 'accepted', 'payment_failed'}, 'cancelled')
    else:
        require(order.buyer_id == user.id, 403, 'not_order_buyer', 'Only the buyer may confirm receipt of delivery.')
        transition(db, order, {'delivered'}, 'completed')
    if data.action in {'reject', 'cancel'}:
        for item in order.items:
            db.execute(update(Produce).where(Produce.id == item.produce_id).values(available_kg=Produce.available_kg + item.quantity_kg))
    order.note = data.note
    for party in [order.buyer, order.farmer]:
        notify(db, party, 'order', f'Order #{order.id}: {order.status.replace("_", " ")}. {data.note}')
    db.flush()
    return order_view(order)
