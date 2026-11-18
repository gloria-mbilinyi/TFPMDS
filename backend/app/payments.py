import hmac
from uuid import uuid4

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .config import MOCK_CALLBACK_SECRET
from .db import get_db
from .errors import require
from .integrations import mobile_money
from .models import Payment, PaymentReceipt, PurchaseOrder, Shipment, TrackingEvent, User
from .notifications import notify
from .orders import accessible, transition
from .schemas import Callback, PaymentCreate, PaymentOutcome
from .security import authorize, current_user, find_or_404
from .views import fields, payment_view

router = APIRouter(prefix='/api/payments', tags=['simulated mobile money'])


def apply_outcome(db, payment, outcome):
    if payment.status != 'pending':
        require(payment.status == outcome, 409, 'terminal_payment', 'A terminal payment outcome cannot be changed.')
        return payment_view(payment)
    result = db.execute(update(Payment).where(Payment.id == payment.id, Payment.status == 'pending').values(status=outcome))
    require(result.rowcount == 1, 409, 'payment_changed', 'Payment changed. Verify its status before retrying.')
    order = find_or_404(db, PurchaseOrder, payment.order_id)
    if outcome == 'successful':
        transition(db, order, {'awaiting_payment'}, 'paid')
        db.add(PaymentReceipt(payment_id=payment.id, order_id=order.id, number=f'TFP-{uuid4().hex[:16].upper()}', amount_tzs=payment.amount_tzs))
        shipment = Shipment(order_id=order.id, tracking_code=f'TZ-{uuid4().hex[:12].upper()}')
        db.add(shipment); db.flush()
        shipment.history.append(TrackingEvent(actor_id=payment.buyer_id, status='pending_arrangement',
                                             location=order.farmer.region, note='Simulated payment confirmed; delivery request created.'))
    else:
        transition(db, order, {'awaiting_payment'}, 'payment_failed' if outcome == 'failed' else 'accepted')
    for party in [order.buyer, order.farmer]:
        notify(db, party, 'payment', f'SIMULATION: payment for order #{order.id} {outcome}. Reference {payment.reference}.')
    db.flush(); db.refresh(payment)
    return payment_view(payment)


@router.post('', status_code=201)
def initiate(data: PaymentCreate, idempotency_key: str = Header(min_length=8, max_length=80),
             user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'buyer')
    order = find_or_404(db, PurchaseOrder, data.order_id)
    require(order.buyer_id == user.id, 403, 'not_order_buyer', 'Only the ordering buyer may initiate payment.')
    previous = db.scalar(select(Payment).where(Payment.buyer_id == user.id, Payment.idempotency_key == idempotency_key))
    if previous:
        require((previous.order_id, previous.provider, previous.phone) == (data.order_id, data.provider, data.phone),
                409, 'idempotency_mismatch', 'This key was already used for different payment details.')
        return payment_view(previous)
    transition(db, order, {'accepted', 'payment_failed'}, 'awaiting_payment')
    reference = mobile_money.initiate(amount_tzs=order.total_tzs, phone=data.phone, provider=data.provider)
    payment = Payment(order_id=order.id, buyer_id=user.id, provider=data.provider, phone=data.phone,
                      amount_tzs=order.total_tzs, reference=reference, idempotency_key=idempotency_key)
    db.add(payment); db.flush()
    return payment_view(payment)


@router.get('')
def transactions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Payment).join(PurchaseOrder, Payment.order_id == PurchaseOrder.id).order_by(Payment.id.desc())
    if user.role not in {'administrator', 'logistics'}:
        query = query.where((PurchaseOrder.buyer_id == user.id) | (PurchaseOrder.farmer_id == user.id))
    return [payment_view(p) for p in db.scalars(query)]


@router.post('/mock-callback')
def callback(data: Callback, x_mock_secret: str = Header(default=''), db: Session = Depends(get_db)):
    require(hmac.compare_digest(x_mock_secret, MOCK_CALLBACK_SECRET), 401, 'invalid_callback', 'Invalid mock-provider callback credentials.')
    payment = db.scalar(select(Payment).where(Payment.reference == data.reference))
    require(payment is not None, 404, 'not_found', 'Payment reference not found.')
    return apply_outcome(db, payment, data.outcome)


@router.get('/{payment_id}')
def status(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = find_or_404(db, Payment, payment_id)
    accessible(find_or_404(db, PurchaseOrder, payment.order_id), user)
    return payment_view(payment)


@router.post('/{payment_id}/simulate')
def simulate(payment_id: int, data: PaymentOutcome, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = find_or_404(db, Payment, payment_id)
    require(payment.buyer_id == user.id, 403, 'not_payment_buyer', 'Only this buyer may run the payment simulation.')
    return apply_outcome(db, payment, data.outcome)


@router.get('/{payment_id}/receipt')
def receipt(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = find_or_404(db, Payment, payment_id)
    order = find_or_404(db, PurchaseOrder, payment.order_id); accessible(order, user)
    record = db.scalar(select(PaymentReceipt).where(PaymentReceipt.payment_id == payment_id))
    require(record is not None, 404, 'receipt_unavailable', 'A receipt is available after successful payment.')
    return {**fields(record, 'id', 'number', 'order_id', 'payment_id', 'amount_tzs', 'created_at'),
            'buyer_name': order.buyer.name, 'farmer_name': order.farmer.name,
            'provider': payment.provider, 'reference': payment.reference, 'currency': 'TZS', 'mode': 'SIMULATION - NO REAL MONEY'}
