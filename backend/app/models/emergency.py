"""
models/emergency.py
---------------------
OWNED BY MEMBER 3 (Faisal) - Emergency Contacts, SOS, Fall Logging,
Daily Safety Check-ins.

Nothing implemented yet - this file intentionally left as a starting
template so you own it cleanly with no conflicts. Example structure below
(commented out) matches the project spec; uncomment and build from there,
or replace entirely with your own design.
"""

# import uuid
# from datetime import datetime
# from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from app.database import Base
#
# class EmergencyContact(Base):
#     __tablename__ = "emergency_contacts"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
#     name = Column(String, nullable=False)
#     phone = Column(String, nullable=False)  # enforce E.164 format, e.g. +8801XXXXXXXXX
#     relationship_label = Column(String, nullable=False)
#     priority = Column(Integer, nullable=False)
#
# class DailyCheckin(Base):
#     __tablename__ = "daily_checkins"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
#     checkin_date = Column(DateTime, nullable=False)
#     checked_in_at = Column(DateTime, nullable=True)
#     status = Column(String, default="PENDING")  # PENDING / COMPLETED / MISSED
