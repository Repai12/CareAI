"""
routers/activity.py
----------------------
Module 1: Activity Tracking (README Features table: "Activity tracking
with trend dashboards"). Patient logs activity; family/doctor see the
same history read-only, same access bar as vitals/mood. Includes
edit/delete from the start (mood tracking was missing this initially -
patients need to be able to fix or remove a mistaken entry).

Endpoints:
    POST   /activity/{patient_id}              - log an entry (patient, self only)
    GET    /activity/{patient_id}               - history (patient self, or active-linked family/doctor)
    PUT    /activity/{patient_id}/{activity_id}  - edit own entry
    DELETE /activity/{patient_id}/{activity_id}  - delete own entry
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.activity import ActivityLog, ActivityType
from app.schemas import ActivityLogCreate, ActivityLogUpdate, ActivityLogOut

router = APIRouter(prefix="/activity", tags=["activity"])

VALID_ACTIVITY_TYPES = {t.value for t in ActivityType}
MAX_DURATION_MINUTES = 1440  # a full day - anything higher is almost certainly a typo


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own activity history")
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
        raise HTTPException(403, "You do not have access to this patient's activity history")


def _validate_type_and_duration(activity_type: str, duration_minutes: int):
    if activity_type not in VALID_ACTIVITY_TYPES:
        raise HTTPException(422, f"activity_type must be one of {sorted(VALID_ACTIVITY_TYPES)}")
    if duration_minutes <= 0 or duration_minutes > MAX_DURATION_MINUTES:
        raise HTTPException(422, f"duration_minutes must be between 1 and {MAX_DURATION_MINUTES}")


@router.post("/{patient_id}", response_model=ActivityLogOut)
def log_activity(
    patient_id: uuid.UUID,
    payload: ActivityLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.patient.value or current_user.id != patient_id:
        raise HTTPException(403, "Only the patient can log their own activity")

    _validate_type_and_duration(payload.activity_type, payload.duration_minutes)

    entry = ActivityLog(
        patient_id=patient_id,
        activity_type=payload.activity_type,
        duration_minutes=payload.duration_minutes,
        note=payload.note.strip() if payload.note else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{patient_id}", response_model=list[ActivityLogOut])
def get_activity_history(
    patient_id: uuid.UUID,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.patient_id == patient_id)
        .order_by(ActivityLog.logged_at.desc())
        .limit(min(limit, 200))
        .all()
    )


@router.put("/{patient_id}/{activity_id}", response_model=ActivityLogOut)
def update_activity(
    patient_id: uuid.UUID,
    activity_id: uuid.UUID,
    payload: ActivityLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(ActivityLog).filter(ActivityLog.id == activity_id, ActivityLog.patient_id == patient_id).first()
    if not entry:
        raise HTTPException(404, "Activity entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only edit your own activity entries")

    new_type = payload.activity_type if payload.activity_type is not None else entry.activity_type
    new_duration = payload.duration_minutes if payload.duration_minutes is not None else entry.duration_minutes
    _validate_type_and_duration(new_type, new_duration)

    entry.activity_type = new_type
    entry.duration_minutes = new_duration
    if payload.note is not None:
        entry.note = payload.note.strip() or None

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{patient_id}/{activity_id}")
def delete_activity(
    patient_id: uuid.UUID,
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(ActivityLog).filter(ActivityLog.id == activity_id, ActivityLog.patient_id == patient_id).first()
    if not entry:
        raise HTTPException(404, "Activity entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only delete your own activity entries")

    db.delete(entry)
    db.commit()
    return {"status": "deleted"}
