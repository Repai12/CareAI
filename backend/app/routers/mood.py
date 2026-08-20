"""
routers/mood.py
------------------
Module 1: Mood Tracking (README Features table). Patient logs how
they're feeling; family/doctor can view the trend read-only, same
access bar as vitals/dashboard.

Endpoints:
    POST /mood/{patient_id}   - log a mood entry (patient, self only)
    GET  /mood/{patient_id}   - recent mood history (patient self, or active-linked family/doctor)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.mood import MoodLog, MoodLevel
from app.schemas import MoodLogCreate, MoodLogOut, MoodLogUpdate

router = APIRouter(prefix="/mood", tags=["mood"])

VALID_MOODS = {m.value for m in MoodLevel}


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own mood history")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's mood history")


@router.post("/{patient_id}", response_model=MoodLogOut)
def log_mood(
    patient_id: uuid.UUID,
    payload: MoodLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.patient.value or current_user.id != patient_id:
        raise HTTPException(403, "Only the patient can log their own mood")

    if payload.mood not in VALID_MOODS:
        raise HTTPException(422, f"mood must be one of {sorted(VALID_MOODS)}")

    entry = MoodLog(
        patient_id=patient_id,
        mood=payload.mood,
        note=payload.note.strip() if payload.note else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{patient_id}", response_model=list[MoodLogOut])
def get_mood_history(
    patient_id: uuid.UUID,
    limit: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(MoodLog)
        .filter(MoodLog.patient_id == patient_id)
        .order_by(MoodLog.logged_at.desc())
        .limit(min(limit, 100))
        .all()
    )


@router.put("/{patient_id}/{mood_id}", response_model=MoodLogOut)
def update_mood(
    patient_id: uuid.UUID,
    mood_id: uuid.UUID,
    payload: MoodLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(MoodLog).filter(MoodLog.id == mood_id, MoodLog.patient_id == patient_id).first()
    if not entry:
        raise HTTPException(404, "Mood entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only edit your own mood entries")

    if payload.mood is not None:
        if payload.mood not in VALID_MOODS:
            raise HTTPException(422, f"mood must be one of {sorted(VALID_MOODS)}")
        entry.mood = payload.mood
    if payload.note is not None:
        entry.note = payload.note.strip() or None

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{patient_id}/{mood_id}")
def delete_mood(
    patient_id: uuid.UUID,
    mood_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(MoodLog).filter(MoodLog.id == mood_id, MoodLog.patient_id == patient_id).first()
    if not entry:
        raise HTTPException(404, "Mood entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only delete your own mood entries")

    db.delete(entry)
    db.commit()
    return {"status": "deleted"}
