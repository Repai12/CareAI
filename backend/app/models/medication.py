"""
models/medication.py
----------------------
OWNED BY MEMBER 2 (Afifa) - Medication Management, Appointments & Prescriptions.

Minimal working versions built by Member 4 as placeholders so the Dashboard
has real data to read. Member 2: extend freely (adherence tracking,
prescriptions, Google Calendar sync fields) - keep the table/class names
below stable, or coordinate a rename with Member 4.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    schedule_time = Column(String, nullable=False)  # e.g. "08:00,20:00"
    active = Column(Boolean, default=True)

    patient = relationship("User", back_populates="medications")


class AppointmentStatus(str, enum.Enum):
    upcoming = "upcoming"
    completed = "completed"
    cancelled = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String, nullable=True)
    status = Column(String, default=AppointmentStatus.upcoming.value)

    patient = relationship("User", back_populates="appointments")
