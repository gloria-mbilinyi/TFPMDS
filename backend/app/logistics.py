from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import PaymentReceipt, PurchaseOrder, Shipment, TrackingEvent, User
from .notifications import notify
from .schemas import Assign, ShipmentUpdate
from .security import authorize, current_user, find_or_404
from .views import shipment_view

router = APIRouter(prefix='/api/shipments', tags=['logistics and shipment tracking'])
SHIPMENT_TRANSITIONS = {
    'pending_arrangement': {'awaiting_transporter', 'assignment_failed'},
    'awaiting_transporter': {'assignment_failed'},
    'assignment_failed': {'awaiting_transporter'},
    'assigned': {'ready_for_pickup', 'assignment_failed'},
    'ready_for_pickup': {'picked_up', 'delivery_failed'},
    'picked_up': {'in_transit', 'delivery_failed'},
    'in_transit': {'delivered', 'delivery_failed'},
    'delivery_failed': {'ready_for_pickup', 'return_requested'},
    'delivered': {'return_requested'},
    'return_requested': {'returned'},
    'returned': set(),
}


def access(shipment, user):
    require(user.role in {'administrator', 'logistics'} or user.id in {shipment.order.buyer_id, shipment.order.farmer_id, shipment.transporter_id},
            403, 'shipment_forbidden', 'This shipment belongs to another account.')


def log_event(db, shipment, user, location, note):
    shipment.history.append(TrackingEvent(actor_id=user.id, status=shipment.status, location=location, note=note))
    for party in [shipment.order.buyer, shipment.order.farmer]:
        notify(db, party, 'delivery', f'Shipment {shipment.tracking_code}: {shipment.status.replace("_", " ")} at {location}. {note}')
    db.flush()


@router.get('')
def list_shipments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Shipment).join(PurchaseOrder).order_by(Shipment.id.desc())
    if user.role == 'transporter':
        query = query.where(Shipment.transporter_id == user.id)
    elif user.role not in {'administrator', 'logistics'}:
        query = query.where((PurchaseOrder.buyer_id == user.id) | (PurchaseOrder.farmer_id == user.id))
    return [shipment_view(s) for s in db.scalars(query)]


@router.get('/{shipment_id}')
def detail(shipment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    shipment = find_or_404(db, Shipment, shipment_id); access(shipment, user)
    return shipment_view(shipment)


@router.post('/{shipment_id}/assign')
def assign(shipment_id: int, data: Assign, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'logistics', 'administrator')
    shipment = find_or_404(db, Shipment, shipment_id)
    require(db.scalar(select(PaymentReceipt).where(PaymentReceipt.order_id == shipment.order_id)) is not None,
            409, 'payment_required', 'Only confirmed payments can trigger shipment arrangements.')
    transporter = find_or_404(db, User, data.transporter_id)
    require(transporter.role == 'transporter' and transporter.active and transporter.status == 'approved',
            422, 'invalid_transporter', 'Select an active approved transporter.')
    result = db.execute(update(Shipment).where(Shipment.id == shipment.id, Shipment.status.in_(
        ['pending_arrangement', 'awaiting_transporter', 'assignment_failed', 'assigned'])).values(status='assigned', transporter_id=transporter.id))
    require(result.rowcount == 1)
    db.refresh(shipment)
    shipment.order.status = 'processing_delivery'
    log_event(db, shipment, user, shipment.order.farmer.region, f'Transporter assigned: {transporter.name}.')
    notify(db, transporter, 'delivery', f'You are assigned shipment {shipment.tracking_code}.')
    return shipment_view(shipment)


@router.post('/{shipment_id}/status')
def progress(shipment_id: int, data: ShipmentUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    shipment = find_or_404(db, Shipment, shipment_id)
    authorize(user, 'transporter', 'logistics', 'administrator')
    require(user.role in {'logistics', 'administrator'} or shipment.transporter_id == user.id,
            403, 'not_assigned', 'Only the assigned transporter or logistics staff may update delivery.')
    require(data.status in SHIPMENT_TRANSITIONS[shipment.status], 409, 'invalid_shipment_transition', 'Shipment cannot move to that state.')
    if data.status in {'awaiting_transporter', 'assignment_failed', 'return_requested'}:
        authorize(user, 'logistics', 'administrator')
    if data.status in {'return_requested', 'delivery_failed', 'assignment_failed'}:
        require(len(data.note.strip()) >= 3, 422, 'exception_reason_required', 'Explain the exception in the tracking note.')
    if data.status in {'ready_for_pickup', 'picked_up', 'in_transit', 'delivered', 'delivery_failed', 'returned'}:
        require(shipment.transporter_id is not None, 409, 'assignment_required', 'Assign a transporter before delivery progress.')
    result = db.execute(update(Shipment).where(Shipment.id == shipment.id, Shipment.status == shipment.status).values(status=data.status))
    require(result.rowcount == 1, 409, 'shipment_changed', 'Shipment changed. Refresh before retrying.')
    db.refresh(shipment)
    if data.status == 'assignment_failed':
        shipment.transporter_id = None
    if data.status in {'in_transit', 'delivered', 'return_requested', 'returned'}:
        shipment.order.status = data.status
    elif data.status == 'ready_for_pickup':
        shipment.order.status = 'processing_delivery'
    log_event(db, shipment, user, data.location, data.note)
    return shipment_view(shipment)
