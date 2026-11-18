from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import Notification, User
from .security import authorize, current_user, find_or_404
from .views import fields

router = APIRouter(prefix='/api', tags=['notifications'])


@router.get('/notifications')
def history(unread_only: bool = False, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc())
    if unread_only:
        query = query.where(Notification.read.is_(False))
    return [fields(n, 'id', 'kind', 'message', 'read', 'sms_status', 'sms_reference', 'created_at') for n in db.scalars(query)]


@router.post('/notifications/read-all')
def read_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(read=True))
    return {'message': 'All your notifications marked as read.'}


@router.post('/notifications/{notification_id}/read')
def mark_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = find_or_404(db, Notification, notification_id)
    require(record.user_id == user.id, 403, 'not_recipient', 'This notification belongs to another account.')
    record.read = True
    return {'message': 'Notification marked as read.'}


@router.get('/admin/sms-log')
def sms_log(user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    return [{**fields(n, 'id', 'user_id', 'kind', 'message', 'sms_status', 'sms_reference', 'created_at'), 'recipient': u.name}
            for n, u in db.execute(select(Notification, User).join(User, Notification.user_id == User.id).order_by(Notification.id.desc()))]
