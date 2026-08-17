from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.emergency import EmergencyContact, SafetyCheckin
from app.models.fall_incident import FallIncident
from app.services.twilio_service import twilio_service

def record_checkin(db: Session, user_id: int):
    """
    Record a daily safety check-in for the user.
    """
    checkin = SafetyCheckin(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        status="completed"
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin

def log_fall_incident(db: Session, user_id: int, severity: str, details: str = None):
    """
    Log a fall incident and automatically dispatch Twilio SMS alerts to emergency contacts.
    """
    fall_entry = FallIncident(
        user_id=user_id,
        severity=severity,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(fall_entry)
    db.commit()
    db.refresh(fall_entry)

    # Fetch emergency contacts for the user
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).all()

    phone_numbers = [c.phone for c in contacts if c.phone]

    if phone_numbers:
        sms_message = (
            f"ALERT: Fall incident recorded! Severity: {severity.upper()}. "
            f"Details: {details or 'No additional details provided.'}"
        )
        try:
            twilio_service.send_sos_alert(phone_numbers, sms_message)
        except Exception:
            # Catch Twilio failure gracefully so DB transaction stays intact
            pass

    return fall_entry

def check_missed_checkins(db: Session, max_hours_allowed: int = 24):
    """
    Background job function to check users who missed daily check-in and alert family members via Twilio.
    """
    threshold_time = datetime.utcnow() - timedelta(hours=max_hours_allowed)
    
    # Query users who have registered emergency contacts
    users_with_contacts = db.query(EmergencyContact.user_id).distinct().all()
    user_ids = [u[0] for u in users_with_contacts]

    for uid in user_ids:
        latest_checkin = db.query(SafetyCheckin).filter(
            SafetyCheckin.user_id == uid
        ).order_by(SafetyCheckin.timestamp.desc()).first()

        if not latest_checkin or latest_checkin.timestamp < threshold_time:
            contacts = db.query(EmergencyContact).filter(
                EmergencyContact.user_id == uid
            ).all()
            
            phone_numbers = [c.phone for c in contacts if c.phone]
            if phone_numbers:
                sms_message = (
                    f"WARNING: Daily Safety Check-in missed for User ID {uid}! "
                    f"No check-in recorded in the last {max_hours_allowed} hours."
                )
                try:
                    twilio_service.send_sos_alert(phone_numbers, sms_message)
                except Exception:
                    pass
