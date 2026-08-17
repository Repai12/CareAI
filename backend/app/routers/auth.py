"""
routers/auth.py
-----------------
SHARED FILE - registration and login for all roles.

Registration behavior:
- role = patient  -> gets a fresh, unique patient_code (e.g. CARE-8921),
  which they share with family/doctors so those accounts can link to them.
- role = family / doctor -> must supply an existing patient's patient_code.
  Registration fails with a clear error if the code doesn't match a real
  patient account, instead of silently creating an orphaned viewer.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.user import User, UserRole, PatientLink
from app.auth import hash_password, verify_password, create_access_token, generate_patient_code

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    patient_code: Optional[str] = None  # required for family/doctor


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
        db.add(PatientLink(
            patient_id=linked_patient.id,
            viewer_id=user.id,
            relationship_label=payload.role.value,
        ))

    db.commit()
    db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "patient_code": user.patient_code,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "role": user.role}
