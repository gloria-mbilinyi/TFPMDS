from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import JWT_SECRET
from .db import get_db
from .errors import require
from .models import RevokedToken, User

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = passwords.hash('unusable-dummy-login-password')


def issue_token(user):
    instant = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user.id), 'jti': str(uuid4()), 'iat': instant,
                       'exp': instant + timedelta(hours=2), 'iss': 'tfpmds', 'aud': 'tfpmds-ui'}, JWT_SECRET, algorithm='HS256')


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'], issuer='tfpmds', audience='tfpmds-ui',
                          options={'require': ['sub', 'jti', 'exp', 'iat', 'iss', 'aud']})
    except jwt.InvalidTokenError:
        require(False, 401, 'invalid_token', 'Your session has expired or is invalid. Please sign in.')


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    require(credentials is not None, 401, 'unauthenticated', 'Please sign in.')
    claims = decode_token(credentials.credentials)
    require(db.get(RevokedToken, claims['jti']) is None, 401, 'revoked_token', 'This session was signed out.')
    try:
        user_id = int(claims['sub'])
    except (ValueError, TypeError):
        require(False, 401, 'invalid_token', 'Invalid session subject.')
    user = db.get(User, user_id)
    require(user is not None and user.active, 401, 'inactive_user', 'Your account is unavailable.')
    return user


def authorize(user, *roles, approved=True):
    require(user.role in roles, 403, 'forbidden', 'Your role cannot perform this action.')
    if approved:
        require(user.status == 'approved', 403, 'approval_required', 'Administrator approval is required.')


def find_or_404(db, model, identity):
    record = db.get(model, identity)
    require(record is not None, 404, 'not_found', 'The requested record was not found.')
    return record
