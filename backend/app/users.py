from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import User
from .notifications import notify
from .schemas import ActiveChange, Approval, Profile, StaffCreate, UserOut
from .security import authorize, current_user, find_or_404, passwords

router = APIRouter(prefix='/api', tags=['users and approvals'])


@router.patch('/users/me', response_model=UserOut)
def update_profile(data: Profile, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for field, value in data.model_dump().items():
        setattr(user, field, value)
    # Material farm changes require renewed verification, while existing orders remain accessible.
    if user.role == 'farmer' and user.status == 'approved':
        user.status = 'pending'
        notify(db, user, 'registration', 'Profile updated. Your farm details require renewed approval.')
    db.flush()
    return user


@router.get('/admin/users', response_model=list[UserOut])
def list_users(user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.post('/admin/users/{user_id}/approval', response_model=UserOut)
def approve(user_id: int, data: Approval, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    target = find_or_404(db, User, user_id)
    require(target.role in {'farmer', 'buyer'}, 409, 'not_trading_account', 'Approval applies to farmers and buyers.')
    require(target.status != data.status, 409, 'already_reviewed', 'This account already has this status.')
    target.status = data.status
    target.verification_note = data.note
    notify(db, target, 'registration', f'Your registration was {data.status}: {data.note}')
    db.flush()
    return target


@router.patch('/admin/users/{user_id}/active', response_model=UserOut)
def set_active(user_id: int, data: ActiveChange, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    require(user_id != user.id, 409, 'self_deactivation', 'You cannot deactivate your own administrator account.')
    target = find_or_404(db, User, user_id)
    target.active = data.active
    db.flush()
    return target


@router.post('/admin/staff', response_model=UserOut, status_code=201)
def create_staff(data: StaffCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator')
    fields = data.model_dump(exclude={'password'})
    fields['email'] = str(fields['email']).lower()
    target = User(**fields, password_hash=passwords.hash(data.password), status='approved')
    db.add(target); db.flush()
    return target


@router.get('/users/transporters', response_model=list[UserOut])
def transporters(user: User = Depends(current_user), db: Session = Depends(get_db)):
    authorize(user, 'administrator', 'logistics')
    return db.scalars(select(User).where(User.role == 'transporter', User.active.is_(True), User.status == 'approved')).all()
