"""
routers/safety_checkin.py
----------------------------
OWNED BY MEMBER 3 (Faisal) - Module 3, Feature 6: Daily Safety Check-in
(README S8.6). The patient taps "I'm okay" once a day; a scheduled job
(see check_missed_checkins below, registered in services/scheduler.py)
runs once daily and SMS-alerts the top-priority emergency contact plus
notifies linked family if no check-in happened that day. This is a
silence-triggered alert - the only one in the app that fires on the
*absence* of an action rather than an action itself, which is why it
needs its own scheduled job instead of living inside the check-in
endpoint the way every other feature's notification does.
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.safety_checkin import SafetyCheckin
from app.models.emergency import EmergencyContact
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.services.sms_service import sms_service
from app.schemas import SafetyCheckinOut

router = APIRouter(prefix="/checkin", tags=["safety checkin"])


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own check-ins")
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
        raise HTTPException(403, "You do not have access to this patient's check-ins")


@router.post("", response_model=SafetyCheckinOut, status_code=status.HTTP_201_CREATED)
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Patient-only, single tap: "I'm okay" (README S8.6 - primary actor is always the patient)."""
    if current_user.role != UserRole.patient.value:
        raise HTTPException(403, "Only the patient can record their own check-in")

    entry = SafetyCheckin(user_id=current_user.id, is_checked_in=True)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{patient_id}/history", response_model=List[SafetyCheckinOut])
def get_checkin_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(SafetyCheckin)
        .filter(SafetyCheckin.user_id == patient_id)
        .order_by(SafetyCheckin.checked_in_at.desc())
        .limit(30)
        .all()
    )


def check_missed_checkins(db: Session) -> None:
    """
    Runs once daily (see services/scheduler.py). For every patient with
    no check-in since midnight today: SMS the top-priority emergency
    contact and write a SAFETY notification for linked family. Only
    patients who have logged in at least once are considered (querying
    `users` directly, not gated on having contacts, since a missed
    check-in with zero contacts should still notify family via the
    in-app notification even if there's no SMS leg - same principle as
    SOS's "still log/notify even with nothing to text").
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    patients = db.query(User).filter(User.role == UserRole.patient.value).all()

    for patient in patients:
        checked_in_today = (
            db.query(SafetyCheckin)
            .filter(SafetyCheckin.user_id == patient.id, SafetyCheckin.checked_in_at >= today_start)
            .first()
        )
        if checked_in_today:
            continue

        contacts = (
            db.query(EmergencyContact)
            .filter(EmergencyContact.user_id == patient.id)
            .order_by(EmergencyContact.priority.asc())
            .all()
        )
        if contacts:
            top_contact = contacts[0]
            try:
                sms_service.send_sos_alert(
                    [top_contact.phone],
                    f"{patient.name} has not completed their daily CareAI safety check-in today.",
                )
            except Exception as e:
                print(f"[safety_checkin] SMS to {top_contact.phone} failed for patient {patient.id}: {e}")

        create_notification(
            db,
            patient_id=patient.id,
            event_type="CHECKIN_MISSED",
            title="Daily check-in missed",
            message=f"{patient.name} has not checked in today.",
            category=NotificationCategory.safety,
        )
