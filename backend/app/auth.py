from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .errors import require
from .models import RevokedToken, User
from .notifications import notify
from .schemas import Login, Register, UserOut
from .security import DUMMY_HASH, bearer, current_user, decode_token, issue_token, passwords

router = APIRouter(prefix='/api/auth', tags=['authentication'])


@router.post('/register', response_model=UserOut, status_code=201)
def register(data: Register, db: Session = Depends(get_db)):
    require(db.scalar(select(User).where(User.email == data.email)) is None, 409, 'email_exists', 'An account with this email already exists.')
    fields = data.model_dump(exclude={'password'})
    user = User(**fields, password_hash=passwords.hash(data.password), status='pending')
    db.add(user)
    db.flush()
    notify(db, user, 'registration', 'Your registration is pending administrator verification.')
    db.flush()
    return user


@router.post('/login')
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    valid = passwords.verify(data.password, user.password_hash if user else DUMMY_HASH)
    require(user is not None and valid and user.active, 401, 'invalid_credentials', 'Incorrect credentials or inactive account.')
    return {'access_token': issue_token(user), 'token_type': 'bearer', 'user': UserOut.model_validate(user)}


@router.get('/me', response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post('/logout')
def logout(user: User = Depends(current_user), credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    claims = decode_token(credentials.credentials)
    db.add(RevokedToken(jti=claims['jti'], expires_at=datetime.fromtimestamp(claims['exp'], timezone.utc)))
    return {'message': 'Signed out. This token is now revoked.'}
