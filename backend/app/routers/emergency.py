"""
routers/emergency.py
----------------------
OWNED BY MEMBER 3 (Faisal) - Module 3: Emergency Contacts + SOS Alert
System (README S6.3/S7.3). This is the highest-stakes feature in the
app, so every corner case in the spec gets handled explicitly rather
than left to "should work":
- No emergency contacts configured -> the SOS event still logs and still
  notifies any linked family/doctor even though there's nothing to text.
- A contact's SMS failing doesn't stop the rest of the batch from
  sending, and the caller is told which contacts succeeded/failed rather
  than a blanket "sent" that might be a lie.
- The SOS event always writes to the shared notifications table
  (category=EMERGENCY) so it shows up in the Family Notification Center
  and doctor's flagged list even if the SMS provider is down entirely.
"""

import threading
import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.emergency import EmergencyContact
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.schemas import EmergencyContactCreate, EmergencyContactUpdate, EmergencyContactOut
from app.services.sms_service import sms_service

router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency Management"]
)


@router.get("/contacts", response_model=List[EmergencyContactOut])
def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id
    ).order_by(EmergencyContact.priority.asc()).all()
    return contacts


@router.post("/contacts", response_model=EmergencyContactOut, status_code=status.HTTP_201_CREATED)
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


@router.put("/contacts/{contact_id}", response_model=EmergencyContactOut)
def update_emergency_contact(
    contact_id: uuid.UUID,
    contact_data: EmergencyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Emergency contact not found")

    for field, value in contact_data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(
    contact_id: uuid.UUID,
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


def _send_sms_batch(phone_numbers: list[str], message: str) -> tuple[list[str], list[str]]:
    """
    Sends to each contact independently so one bad number/provider hiccup
    doesn't silently swallow the rest of the batch. Returns
    (delivered_numbers, failed_numbers) - used to build an honest status
    message rather than a blanket "sent".
    """
    delivered, failed = [], []
    for phone in phone_numbers:
        try:
            sms_service.send_sos_alert([phone], message)
            delivered.append(phone)
        except Exception:
            failed.append(phone)
    return delivered, failed


# Rapid-repeat guard: an anxious user (or a child, or a stuck/mashed
# button) tapping SOS several times in a few seconds shouldn't fire off
# a fresh SMS batch and a fresh notification-feed entry every single
# time - that's alarming noise for family/doctor, not more safety. This
# deliberately does NOT block a genuine second emergency a few minutes
# later, or even a deliberate retry after the cooldown - it only
# collapses truly rapid repeats into the original result. In-memory,
# same simple pattern as auth.py's login rate limiter - fine for this
# project's single-process deployment.
#
# _sos_lock guards against two nearly-simultaneous requests (e.g. a
# double-click, or two browser tabs on the same account) both reading
# "no cooldown yet" before either has written its claim - without the
# lock, both slip through and each sends its own SMS batch + creates
# its own notification, exactly the noise this guard exists to prevent.
# The slot is claimed (result=None) *before* the actual send/notify
# work, not after, so a request arriving mid-send still sees it.
_SOS_COOLDOWN_SECONDS = 10
_recent_sos: dict[str, dict] = {}
_sos_lock = threading.Lock()


@router.post("/sos", status_code=status.HTTP_200_OK)
def trigger_sos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = time.time()
    uid = str(current_user.id)
    with _sos_lock:
        cached = _recent_sos.get(uid)
        if cached and now - cached["at"] < _SOS_COOLDOWN_SECONDS:
            if cached["result"] is not None:
                seconds_ago = int(now - cached["at"])
                return {
                    **cached["result"],
                    "message": f"SOS already triggered {seconds_ago}s ago - your contacts have already been notified.",
                    "already_sent": True,
                }
            # An identical request is still mid-flight (claimed a moment
            # ago, hasn't finished sending yet) - don't start a second
            # SMS batch, just acknowledge it's already happening.
            return {
                "status": "success",
                "message": "Your SOS is already being sent.",
                "delivered_to": [],
                "failed_to": [],
                "already_sent": True,
            }
        _recent_sos[uid] = {"at": now, "result": None}

    try:
        contacts = db.query(EmergencyContact).filter(
            EmergencyContact.user_id == current_user.id
        ).order_by(EmergencyContact.priority.asc()).all()

        phone_numbers = [c.phone for c in contacts if c.phone]
        sms_message = f"EMERGENCY SOS ALERT! {current_user.name or current_user.email} needs immediate assistance!"

        # The event always logs and always notifies linked family/doctor,
        # even with zero contacts or a total SMS-provider outage - the UI should
        # already have nudged the patient to add contacts (README S6.3), but
        # a real emergency must never silently notify nobody just because
        # that nudge was ignored.
        delivered, failed = _send_sms_batch(phone_numbers, sms_message) if phone_numbers else ([], [])

        if not phone_numbers:
            delivery_note = "No emergency contacts on file - no SMS could be sent."
        elif failed:
            delivery_note = f"SMS delivered to {len(delivered)}/{len(phone_numbers)} contacts. Failed: {len(failed)}."
        else:
            delivery_note = f"SMS delivered to all {len(delivered)} contacts."

        create_notification(
            db,
            patient_id=current_user.id,
            event_type="SOS_TRIGGERED",
            title="SOS alert triggered",
            message=f"{current_user.name} triggered an emergency SOS. {delivery_note}",
            category=NotificationCategory.emergency,
        )

        result = {
            "status": "success",
            "message": f"SOS Alert processed for {len(phone_numbers)} contacts",
            "delivered_to": delivered,
            "failed_to": failed,
            "already_sent": False,
        }
        with _sos_lock:
            _recent_sos[uid] = {"at": now, "result": result}
        return result
    except Exception:
        # Something failed mid-send (DB error, unexpected exception) -
        # release the claim so a retry isn't stuck being told "already
        # sent" for a request that never actually completed.
        with _sos_lock:
            _recent_sos.pop(uid, None)
        raise
