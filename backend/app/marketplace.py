from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import MarketPrice, Produce, User
from .security import find_or_404
from .errors import require
from .views import produce_view

router = APIRouter(prefix='/api', tags=['marketplace'])


@router.get('/produce')
def search(q: str = Query('', max_length=100), crop: str = Query('', max_length=50),
           region: str = Query('', max_length=60), min_price: int = Query(0, ge=0),
           max_price: int | None = Query(None, gt=0), min_quantity: int = Query(0, ge=0),
           farmer_id: int | None = None, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200),
           db: Session = Depends(get_db)):
    query = select(Produce, User).join(User, User.id == Produce.farmer_id).where(
        Produce.active.is_(True), User.status == 'approved', User.active.is_(True),
        Produce.available_kg >= max(1, min_quantity), Produce.price_tzs >= min_price)
    if q:
        query = query.where(or_(Produce.name.ilike(f'%{q}%'), Produce.crop.ilike(f'%{q}%')))
    if crop:
        query = query.where(Produce.crop.ilike(crop))
    if region:
        query = query.where(User.region.ilike(region))
    if max_price is not None:
        query = query.where(Produce.price_tzs <= max_price)
    if farmer_id is not None:
        query = query.where(Produce.farmer_id == farmer_id)
    return [produce_view(p, u) for p, u in db.execute(query.order_by(Produce.created_at.desc()).offset(offset).limit(limit))]


@router.get('/produce/{produce_id}')
def detail(produce_id: int, db: Session = Depends(get_db)):
    record = find_or_404(db, Produce, produce_id)
    farmer = find_or_404(db, User, record.farmer_id)
    require(record.active and farmer.active and farmer.status == 'approved', 404, 'not_available', 'This listing is not currently available.')
    return produce_view(record, farmer)


@router.get('/market-prices')
def market_prices(db: Session = Depends(get_db)):
    return db.scalars(select(MarketPrice).order_by(MarketPrice.crop, MarketPrice.region)).all()
