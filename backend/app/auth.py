"""
auth.py
-------
SHARED FILE - password hashing, JWT tokens, refresh-token/reset-token
helpers, and patient-code generation. One person should "own"
merge-reviewing changes here since every feature depends on it. Talk
before restructuring.
"""

import hashlib
import random
import secrets
import string
import time
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def generate_patient_code(db: Session) -> str:
    """
    Generates a unique, shareable code like CARE-8921 that family/doctor
    accounts use to link themselves to this patient at registration.
    Retries on the rare collision.
    """
    while True:
        code = "CARE-" + "".join(random.choices(string.digits, k=4))
        exists = db.query(User).filter(User.patient_code == code).first()
        if not exists:
            return code


# ---------------------------------------------------------------------
# Refresh tokens
#
# The access token is short-lived (15 min, README S3.2) so it's cheap to
# leave in memory on the frontend. The refresh token is long-lived (7
# days) and lives in an httpOnly cookie instead, and its hash is stored
# server-side in `refresh_tokens` so a single session (logout) or every
# session for a user ("logout everywhere" in /settings) can be revoked
# on demand - a bare JWT can't be revoked before it expires on its own.
# ---------------------------------------------------------------------

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------
# Email verification / password reset tokens
#
# Plain random tokens (not JWTs) stored on the user row so they're
# trivially single-use: redeeming one just clears the column, no
# separate blacklist needed.
# ---------------------------------------------------------------------

def generate_email_token() -> str:
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------
# Login rate limiting (README S3.2: 5 attempts / 15 min, per IP + email)
#
# In-memory sliding window. This is intentionally simple rather than a
# Redis-backed limiter - correct for this project's single-process
# uvicorn deployment, but note for whoever deploys this that it resets
# on restart and does not share state across multiple worker processes.
# ---------------------------------------------------------------------

_LOGIN_ATTEMPT_WINDOW_SECONDS = 15 * 60
_LOGIN_ATTEMPT_MAX = 5
_login_attempts: dict[str, list[float]] = {}


def check_login_rate_limit(key: str) -> None:
    """Raises 429 if `key` (ip+email) has too many recent failed logins."""
    now = time.time()
    attempts = [t for t in _login_attempts.get(key, []) if now - t < _LOGIN_ATTEMPT_WINDOW_SECONDS]
    _login_attempts[key] = attempts
    if len(attempts) >= _LOGIN_ATTEMPT_MAX:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts. Please try again in 15 minutes.",
        )


def record_failed_login(key: str) -> None:
    _login_attempts.setdefault(key, []).append(time.time())


def clear_login_attempts(key: str) -> None:
    _login_attempts.pop(key, None)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
