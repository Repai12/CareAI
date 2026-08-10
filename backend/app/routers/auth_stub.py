"""
auth_stub.py
------------
Temporary register/login endpoints, ONLY so you can get a JWT token to test
the Dashboard and Weekly Report endpoints while the team's real shared auth
module isn't built yet. Mention this clearly to your evaluator - this is a
stand-in, not one of your 4 graded features.

Registration behavior:
- role = patient  -> account created standalone, no linking needed.
- role = family / doctor -> must supply the patient's email so we can
  create a PatientLink automatically. If that email doesn't belong to an
  existing patient account, registration fails with a clear error instead
  of silently creating an orphaned account.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, PatientLink
from app.auth import hash_password, verify_password, create_access_token
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth (stub)"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    patient_email: Optional[EmailStr] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    linked_patient = None
    if payload.role in (UserRole.family, UserRole.doctor):
        if not payload.patient_email:
            raise HTTPException(
                400,
                f"As a {payload.role.value}, you must provide the patient's email to link your account.",
            )
        linked_patient = (
            db.query(User)
            .filter(User.email == payload.patient_email, User.role == UserRole.patient)
            .first()
        )
        if not linked_patient:
            raise HTTPException(
                404,
                "No patient account found with that email. Ask the patient to register first.",
            )

    user = User(
        id=uuid.uuid4(),
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    if linked_patient:
        db.add(PatientLink(
            patient_id=linked_patient.id,
            viewer_id=user.id,
            relationship_label=payload.role.value,
        ))

    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "role": user.role}