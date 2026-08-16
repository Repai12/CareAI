"""
routers/ai_summary.py
------------------------
OWNED BY MEMBER 4 (Repai) - Module 3, Feature 7: Doctor AI Patient
Summary Email. Only doctors can trigger this (per RBAC spec - "Full
Access: Health Overview Dashboard & On-Demand AI Summary Email" is a
doctor-only permission).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, PatientLink
from app.schemas import EmailLogOut
from app.services.ai_summary_service import generate_doctor_ai_summary, RateLimitedError

router = APIRouter(prefix="/reports", tags=["ai summary"])


@router.post("/ai-summary/{patient_id}", response_model=EmailLogOut)
def trigger_ai_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.doctor.value:
        raise HTTPException(403, "Only doctors can generate an AI patient summary")

    # Doctor must actually be linked to this patient
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You are not linked to this patient")

    try:
        return generate_doctor_ai_summary(db, patient_id, current_user)
    except RateLimitedError as e:
        raise HTTPException(429, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
