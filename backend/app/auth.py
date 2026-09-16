import hashlib, hmac, secrets
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from .db import get_db
from .models import User
from .config import settings

def hash_password(value):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', value.encode(), salt.encode(), 600000).hex()
    return salt + ':' + digest

def verify_password(value, stored):
    salt, expected = stored.split(':')
    actual = hashlib.pbkdf2_hmac('sha256', value.encode(), salt.encode(), 600000).hex()
    return hmac.compare_digest(actual, expected)

def token(user):
    return jwt.encode({'sub': str(user.id), 'v': user.token_version, 'exp': datetime.now(timezone.utc) + timedelta(hours=8)}, settings.secret_key, algorithm='HS256')

def current_user(request: Request, db=Depends(get_db)):
    value = request.cookies.get('session')
    if not value:
        raise HTTPException(401, 'Vui lòng đăng nhập.')
    try:
        payload = jwt.decode(value, settings.secret_key, algorithms=['HS256'])
        user = db.get(User, int(payload['sub']))
        if not user or not user.active or payload['v'] != user.token_version:
            raise ValueError()
        return user
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, 'Phiên đăng nhập đã hết hạn.')

def roles(*allowed):
    def check(user=Depends(current_user)):
        if user.role not in allowed:
            raise HTTPException(403, 'Bạn không có quyền thực hiện thao tác này.')
        return user
    return check

staff = roles('manager', 'pharmacist')
ai_user = roles('manager', 'pharmacist', 'cashier')
manager = roles('manager')
