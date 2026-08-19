"""
routers/fall_incidents.py
----------------------------
OWNED BY MEMBER 3 (Faisal) - Module 3, Feature 5: Fall Incident Logger
(README S8.5). Patient or a family member with manage permission can log
a fall; anything above "minor" severity auto-SMS's the patient's
emergency contacts, following the same per-contact delivery-status logic
as SOS (S7.3) rather than a blanket "sent".
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from app.models.fall_incident import FallIncident
from app.models.emergency import EmergencyContact
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.services.twilio_service import twilio_service
from app.schemas import FallIncidentCreate, FallIncidentOut

router = APIRouter(prefix="/fall-incidents", tags=["fall incidents"])

MINOR_SEVERITY = "minor"


def _assert_can_manage(patient_id: uuid.UUID, current_user: User, db: Session):
    """Patient acting on their own record, or an active family/doctor link with manage permission."""
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only log falls for themselves")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
            CareLink.permission_level == CareLinkPermission.view_and_manage.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have permission to log a fall for this patient")


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own records")
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
        raise HTTPException(403, "You do not have access to this patient's records")


@router.post("/{patient_id}", response_model=FallIncidentOut, status_code=status.HTTP_201_CREATED)
def log_fall_incident(
    patient_id: uuid.UUID,
    payload: FallIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)

    entry = FallIncident(user_id=patient_id, severity=payload.severity, details=payload.details)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    patient = db.query(User).filter(User.id == patient_id).first()
    delivered, failed = [], []
    if payload.severity.lower() != MINOR_SEVERITY:
        contacts = (
            db.query(EmergencyContact)
            .filter(EmergencyContact.user_id == patient_id)
            .order_by(EmergencyContact.priority.asc())
            .all()
        )
        phone_numbers = [c.phone for c in contacts if c.phone]
        sms_message = (
            f"ALERT: {patient.name} had a fall (severity: {payload.severity}). "
            f"{payload.details or 'No additional details provided.'}"
        )
        for phone in phone_numbers:
            try:
                twilio_service.send_sos_alert([phone], sms_message)
                delivered.append(phone)
            except Exception:
                failed.append(phone)

    delivery_note = ""
    if payload.severity.lower() != MINOR_SEVERITY:
        if not delivered and not failed:
            delivery_note = " No emergency contacts on file - no SMS could be sent."
        elif failed:
            delivery_note = f" SMS delivered to {len(delivered)}/{len(delivered) + len(failed)} contacts."
        else:
            delivery_note = f" SMS delivered to all {len(delivered)} contacts."

    create_notification(
        db,
        patient_id=patient_id,
        event_type="FALL_LOGGED",
        title="Fall incident logged",
        message=f"A fall was logged for {patient.name} (severity: {payload.severity}).{delivery_note}",
        category=NotificationCategory.emergency,
    )

    return entry


@router.get("/{patient_id}", response_model=List[FallIncidentOut])
def get_fall_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(FallIncident)
        .filter(FallIncident.user_id == patient_id)
        .order_by(FallIncident.occurred_at.desc())
        .all()
    )
