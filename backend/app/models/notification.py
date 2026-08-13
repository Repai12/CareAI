"""
models/notification.py
------------------------
OWNED BY MEMBER 4 (Repai) - for the not-yet-built Family Notification
Center (Module 3, Feature 8). Placeholder only - build out when you get
to that feature.
"""

# import uuid
# from datetime import datetime
# from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from app.database import Base
#
# class Notification(Base):
#     __tablename__ = "notifications"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
#     event_type = Column(String, nullable=False)   # SOS, FALL, MED_MISSED, APPT
#     title = Column(String, nullable=False)
#     message = Column(String, nullable=False)
#     category = Column(String, nullable=False)     # EMERGENCY, MEDICATION, SAFETY
#     is_read = Column(Boolean, default=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
