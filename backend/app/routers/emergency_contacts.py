import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import EmergencyContact, User
from app.schemas import EmergencyContactCreate, EmergencyContactOut, EmergencyContactUpdate

router = APIRouter(prefix="/emergency-contacts", tags=["emergency contacts"])


@router.post("", response_model=EmergencyContactOut)
def create_emergency_contact(
    payload: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = EmergencyContact(
        id=uuid.uuid4(),
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


@router.get("", response_model=list[EmergencyContactOut])
def get_emergency_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .order_by(EmergencyContact.priority.asc())
        .all()
    )


@router.put("/{contact_id}", response_model=EmergencyContactOut)
def update_emergency_contact(
    contact_id: uuid.UUID,
    payload: EmergencyContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == current_user.id,
        )
        .first()
    )

    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    contact.name = payload.name
    contact.phone = payload.phone
    contact.relationship = payload.relationship
    contact.priority = payload.priority

    db.commit()
    db.refresh(contact)

    return contact


@router.delete("/{contact_id}")
def delete_emergency_contact(
    contact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = (
        db.query(EmergencyContact)
        .filter(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == current_user.id,
        )
        .first()
    )

    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    db.delete(contact)
    db.commit()

    return {"message": "Emergency contact deleted successfully"}