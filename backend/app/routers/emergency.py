import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, EmergencyContact
from app.schemas import (
    EmergencyContactCreate,
    EmergencyContactUpdate,
    EmergencyContactOut,
)
from app.services.twilio_service import send_sms

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency Contacts"]
)


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



@router.post("/sos")
def trigger_sos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )

    if not contacts:
        raise HTTPException(
            status_code=404,
            detail="No emergency contacts registered"
        )

    message = (
        f"EMERGENCY ALERT from CareAI! "
        f"{current_user.name} has triggered an SOS alert. "
        f"Please contact them immediately."
    )

    sent = []
    failed = []

    for contact in contacts:
        try:
            result = send_sms(contact.phone, message)

            sent.append({
                "contact": contact.name,
                "phone": contact.phone,
                "message_sid": result.sid
            })

        except Exception as e:
            failed.append({
                "contact": contact.name,
                "phone": contact.phone,
                "error": str(e)
            })

    if not sent:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "SOS triggered but no SMS could be sent",
                "failed": failed
            }
        )

    return {
        "message": "SOS alert processed",
        "total_contacts": len(contacts),
        "messages_sent": len(sent),
        "messages_failed": len(failed),
        "sent": sent,
        "failed": failed
    }