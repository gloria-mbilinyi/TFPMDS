from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import Produce, User
from .schemas import ProduceEdit, ProduceInput
from .security import authorize, current_user, find_or_404
from .views import produce_view

router = APIRouter(prefix='/api/produce', tags=['produce management'])


@router.get('/mine')
def own_produce(user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'farmer', approved=False)
    return [produce_view(p, user) for p in db.scalars(select(Produce).where(Produce.farmer_id == user.id).order_by(Produce.id.desc()))]


@router.post('', status_code=201)
def create(data: ProduceInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'farmer')
    record = Produce(farmer_id=user.id, **data.model_dump())
    db.add(record); db.flush()
    return produce_view(record, user)


@router.patch('/{produce_id}')
def edit(produce_id: int, data: ProduceEdit, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'farmer')
    record = find_or_404(db, Produce, produce_id)
    require(record.farmer_id == user.id, 403, 'not_owner', 'Only the listing farmer may edit it.')
    require(record.active, 409, 'inactive_listing', 'Deactivated listings are retained for order history. Create a new listing.')
    for key, value in data.model_dump().items():
        setattr(record, key, value)
    db.flush()
    return produce_view(record, user)


@router.delete('/{produce_id}')
def deactivate(produce_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'farmer')
    record = find_or_404(db, Produce, produce_id)
    require(record.farmer_id == user.id, 403, 'not_owner', 'Only the listing farmer may deactivate it.')
    record.active = False
    return {'message': 'Listing deactivated; existing order history retained.'}
