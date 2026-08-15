"""
services/notification_service.py
------------------------------------
OWNED BY MEMBER 4 (Repai).

create_notification() is the ONE function every feature should call to
add an event to the Family Notification Center - Member 1, 2, 3: import
this into your own routers/services and call it whenever something
happens a family member should know about (SOS triggered, medication
missed, appointment booked, daily check-in missed, etc). You don't need
to touch this file to use it, just import and call.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationCategory


def create_notification(
    db: Session,
    patient_id: uuid.UUID,
    event_type: str,
    title: str,
    message: str,
    category: NotificationCategory,
) -> Notification:
    notification = Notification(
        patient_id=patient_id,
        event_type=event_type,
        title=title,
        message=message,
        category=category.value,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
