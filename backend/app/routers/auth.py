"""
routers/auth.py
-----------------
SHARED FILE - registration, login, password reset, and session management
(refresh/logout) for all roles.

Registration behavior:
- role = patient  -> gets a fresh, unique patient_code (e.g. CARE-8921),
  which they share with family/doctors so those accounts can link to them.
- role = family / doctor -> must supply an existing patient's patient_code.
  Registration fails with a clear error if the code doesn't match a real
  patient account, instead of silently creating an orphaned viewer.
- role = doctor -> flagged unverified (README S13 "known gap"): a license
  number is required but never checked against a real registry, so the
  response includes a warning the frontend should render as a badge.
- Accounts are usable immediately after registration - no emailed
  verification link to click. That gate existed originally (README
  S3.1/3.2) but was dropped: the team's Resend account has no verified
  domain, so its sandbox mode can only deliver to one hardcoded inbox -
  nobody else (teammates testing with their own address, a grader) could
  ever receive the link, permanently locking their own account out.

Session model (README S3.2/3.4):
- POST /login returns a short-lived access token in the JSON body (15
  min - the frontend is expected to hold it in memory) and sets a
  longer-lived refresh token as an httpOnly cookie (7 days).
- POST /refresh exchanges a valid, non-revoked refresh cookie for a new
  access token, and rotates the refresh token (old one is revoked, a new
  one issued) so a stolen refresh token can't be replayed indefinitely.
- POST /logout revokes just the current refresh token. POST /logout-all
  revokes every refresh token for the account ("logout everywhere" for a
  lost/shared elderly-user device, README S3.4).
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission, RefreshToken
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_patient_code,
    generate_refresh_token,
    hash_token,
    generate_email_token,
    check_login_rate_limit,
    record_failed_login,
    clear_login_attempts,
    get_current_user,
)
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
RESET_TOKEN_TTL_HOURS = 1


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    patient_code: Optional[str] = None  # required for family/doctor
    license_number: Optional[str] = None  # required for doctor


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str


def _try_send_email(to_email: str, subject: str, html_content: str) -> None:
    """
    Best-effort send - never lets an email outage block the core action
    (registration, password reset) from succeeding, per the app-wide
    third-party-failure rule in README S11. Failures are printed for now
    since there's no admin-facing delivery log for auth emails yet.
    """
    try:
        send_email(to_email=to_email, subject=subject, html_content=html_content)
    except Exception as e:
        print(f"[auth email] failed to send to {to_email}: {e}")


def _issue_refresh_token(db: Session, user_id) -> str:
    raw_token = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    return raw_token


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=False,  # set True once served over HTTPS in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",
    )


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    linked_patient = None
    new_patient_code = None

    if payload.role == UserRole.patient:
        new_patient_code = generate_patient_code(db)
    else:
        if payload.role == UserRole.doctor and not payload.license_number:
            raise HTTPException(400, "A medical license/registration number is required to register as a doctor.")
        if not payload.patient_code:
            raise HTTPException(
                400,
                f"As a {payload.role.value}, you must provide the patient's code to link your account.",
            )
        linked_patient = (
            db.query(User)
            .filter(User.patient_code == payload.patient_code, User.role == UserRole.patient.value)
            .first()
        )
        if not linked_patient:
            raise HTTPException(
                404,
                "No patient found with that code. Double check the code with the patient.",
            )

    user = User(
        id=uuid.uuid4(),
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        patient_code=new_patient_code,
    )
    db.add(user)
    db.flush()

    if linked_patient:
        # Pending, not active - the patient has to approve this before any
        # data actually flows (README S4.2/S13: never auto-active).
        # Doctors default to view_and_manage for clinical entries, family
        # defaults to view_only unless the patient upgrades it later (S4.3).
        default_permission = (
            CareLinkPermission.view_and_manage if payload.role == UserRole.doctor else CareLinkPermission.view_only
        )
        db.add(CareLink(
            patient_id=linked_patient.id,
            viewer_id=user.id,
            link_role=payload.role.value,
            relationship_label=payload.role.value,
            permission_level=default_permission.value,
            status=CareLinkStatus.pending.value,
            invited_by=user.id,
        ))

    db.commit()
    db.refresh(user)

    if linked_patient:
        create_notification(
            db,
            patient_id=linked_patient.id,
            event_type="CONNECTION_REQUEST",
            title="New connection request",
            message=f"{user.name} wants to connect as your {payload.role.value}. Review it in your connections.",
            category=NotificationCategory.connection,
        )

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "patient_code": user.patient_code,
        "doctor_unverified_notice": (
            "Doctor accounts are not checked against a real license registry in this "
            "version - your account is marked unverified until an admin reviews it."
            if payload.role == UserRole.doctor else None
        ),
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{client_ip}:{payload.email}"
    check_login_rate_limit(rate_limit_key)

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        record_failed_login(rate_limit_key)
        raise HTTPException(401, "Invalid credentials")

    clear_login_attempts(rate_limit_key)

    access_token = create_access_token(user.id)
    refresh_token = _issue_refresh_token(db, user.id)
    db.commit()
    _set_refresh_cookie(response, refresh_token)

    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Exchanges the httpOnly refresh cookie for a new access token, and
    rotates the refresh token itself. This is what the frontend calls
    silently in the background when the access token expires (README
    S3.5) instead of bouncing straight to /login.
    """
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(401, "No refresh token provided")

    token_hash = hash_token(raw_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not stored or stored.revoked_at is not None or stored.expires_at < datetime.utcnow():
        raise HTTPException(401, "Refresh token is invalid or expired. Please log in again.")

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user:
        raise HTTPException(401, "Account no longer exists")

    # Rotate: revoke the used token, issue a fresh one.
    stored.revoked_at = datetime.utcnow()
    new_refresh_token = _issue_refresh_token(db, user.id)
    db.commit()
    _set_refresh_cookie(response, new_refresh_token)

    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        token_hash = hash_token(raw_token)
        stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.utcnow()
            db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")
    return {"message": "Logged out"}


@router.post("/logout-all")
def logout_all(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes every refresh token for the account - "logout everywhere" in /settings."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.utcnow()})
    db.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")
    return {"message": "Logged out of all sessions"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Always the same response whether or not the email exists, so this
    # endpoint can't be used to enumerate registered accounts (README S3.3).
    generic_response = {"message": "If that email is registered, a reset link has been sent."}

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return generic_response

    reset_token = generate_email_token()
    user.reset_token = reset_token
    user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_TTL_HOURS)
    db.commit()

    reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token}"
    _try_send_email(
        to_email=user.email,
        subject="Reset your CareAI password",
        html_content=(
            f"<p>Hi {user.name},</p>"
            f"<p>Reset your CareAI password using the link below:</p>"
            f'<p><a href="{reset_url}">{reset_url}</a></p>'
            f"<p>This link expires in {RESET_TOKEN_TTL_HOURS} hour and can only be used once. "
            f"If you didn't request this, you can ignore this email.</p>"
        ),
    )
    return generic_response


@router.post("/reset-password/{token}")
def reset_password(token: str, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(400, "Invalid or already-used reset link.")
    if user.reset_token_expires_at and user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(400, "This reset link has expired. Please request a new one.")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None

    # A stolen device shouldn't stay logged in after a password reset -
    # revoke every existing refresh token for this account (README S3.3).
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.utcnow()})

    db.commit()
    return {"message": "Password has been reset. Please log in again."}
