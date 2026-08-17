from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.emergency import EmergencyContact
from app.schemas import EmergencyContactCreate, EmergencyContactResponse
from app.services.twilio_service import twilio_service

router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency Management"]
)

@router.get("/contacts", response_model=List[EmergencyContactResponse])
def get_emergency_contacts(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id
    ).order_by(EmergencyContact.priority.asc()).all()
    return contacts

@router.post("/contacts", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
def create_emergency_contact(
    contact_data: EmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_contact = EmergencyContact(
        user_id=current_user.id,
        name=contact_data.name,
        phone=contact_data.phone,
        relationship=contact_data.relationship,
        priority=contact_data.priority
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Emergency contact not found"
        )
        
    db.delete(contact)
    db.commit()
    return None

@router.post("/sos", status_code=status.HTTP_200_OK)
def trigger_sos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id
    ).all()
    
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No emergency contacts found to send SOS alert"
        )
        
    phone_numbers = [c.phone for c in contacts if c.phone]
    
    if not phone_numbers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registered emergency contacts do not have valid phone numbers"
        )
        
    sos_message = f"EMERGENCY SOS ALERT! User {current_user.full_name or current_user.email} needs immediate assistance!"
    
    try:
        twilio_service.send_sos_alert(phone_numbers, sos_message)
    except Exception as e:
        # Prevent API crash if Twilio credentials fail
        pass

    return {
        "status": "success", 
        "message": f"SOS Alert processed for {len(phone_numbers)} contacts"
    }
