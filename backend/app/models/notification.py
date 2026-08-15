"""
models/notification.py
------------------------
OWNED BY MEMBER 4 (Repai) - Module 3, Feature 8: Family Notification
Center. This is the shared event feed every feature can write into -
see services/notification_service.py for the one function everyone
should call to add an event here (Members 1/2/3: this is how your
SOS alerts, medication taken/missed, and appointment events show up
in the family's feed once you wire your triggers to call it).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class NotificationCategory(str, enum.Enum):
    emergency = "EMERGENCY"     # Member 3 - SOS, falls
    medication = "MEDICATION"   # Member 2 - taken/missed
    appointment = "APPOINTMENT"  # Member 2 - booked/cancelled, also Member 4's report/summary events
    safety = "SAFETY"           # Member 3 - missed check-ins


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)   # e.g. "SOS", "MED_TAKEN", "REPORT_SENT"
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    category = Column(String, nullable=False)     # NotificationCategory value
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Speeds up the two queries the feed actually runs: "unread events
        # for this patient" and "events for this patient, newest first".
        Index("ix_notifications_patient_created", "patient_id", "created_at"),
    )
