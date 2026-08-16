import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, EmergencyContact, FallIncident, SafetyCheckin
from app.services.twilio_service import send_sms
from app.services.safety_checkin_service import start_safety_checkin_scheduler
from app.schemas import (
    EmergencyContactCreate,
    EmergencyContactUpdate,
    EmergencyContactOut,
    FallIncidentCreate,
    FallIncidentOut,
    SafetyCheckinOut,
)

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency Contacts"]
)
start_safety_checkin_scheduler()

@router.post(
    "/contacts",
    response_model=EmergencyContactOut,
    status_code=201
)
def create_emergency_contact(
    payload: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = EmergencyContact(
        user_id=current_user.id,
        name=payload.name,
        phone=payload.phone,
        relationship=payload.relationship,
        priority=payload.priority,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


@router.get(
    "/contacts",
    response_model=list[EmergencyContactOut]
)
def get_emergency_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )


@router.get(
    "/contacts/{contact_id}",
    response_model=EmergencyContactOut
)
def get_emergency_contact(
    contact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == current_user.id
        )
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Emergency contact not found"
        )

    return contact


@router.put(
    "/contacts/{contact_id}",
    response_model=EmergencyContactOut
)
def update_emergency_contact(
    contact_id: uuid.UUID,
    payload: EmergencyContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == current_user.id
        )
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Emergency contact not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return contact


@router.delete(
    "/contacts/{contact_id}"
)
def delete_emergency_contact(
    contact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == current_user.id
        )
        .first()
    )

    if not contact:
        raise HTTPException(
            status_code=404,
            detail="Emergency contact not found"
        )

    db.delete(contact)
    db.commit()

    return {
        "message": "Emergency contact deleted successfully"
    }


@router.post(
    "/falls",
    response_model=FallIncidentOut,
    status_code=201
)
def log_fall_incident(
    payload: FallIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )

    incident = FallIncident(
        user_id=current_user.id,
        severity=payload.severity,
        details=payload.details,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    message = (
        f"CAREAI FALL ALERT! "
        f"{current_user.name} has reported a fall. "
        f"Severity: {payload.severity}. "
        f"Details: {payload.details or 'No additional details.'}"
    )

    for contact in contacts:
        try:
            send_sms(contact.phone, message)
        except Exception:
            pass

    return incident


@router.post(
    "/checkin",
    response_model=SafetyCheckinOut,
    status_code=201
)
def daily_safety_checkin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    checkin = SafetyCheckin(
        user_id=current_user.id
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return checkin
