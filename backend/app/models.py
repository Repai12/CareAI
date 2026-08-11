"""
models.py
---------
SQLAlchemy ORM models = the real Postgres tables.

NOTE FOR THE TEAM: `User`, `Vitals`, `Medication`, and `Appointment` are shared
tables that Member-1, Member-2 and Member-3 will also write to from their own
features (vitals logging, medication management, appointment booking).
I (Member-4) only need to READ from them for the dashboard, and I've added
minimal versions here so my feature runs end-to-end on its own branch.
When we merge branches, we'll reconcile these with whoever "owns" each table
so we don't end up with duplicate/conflicting model definitions.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    patient = "patient"
    family = "family"
    doctor = "doctor"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    vitals = relationship("Vitals", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    emergency_contacts = relationship(
    "EmergencyContact",
    back_populates="patient",
    cascade="all, delete-orphan"
)

class PatientLink(Base):
    """
    Links a family member or doctor account to the patient(s) they can view.
    Needed so the dashboard knows *which* patients a family/doctor user is
    allowed to see (real relational data, not hardcoded IDs).
    """
    __tablename__ = "patient_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    viewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # family or doctor
    relationship_label = Column(String, default="family")  # "family" or "doctor"


class Vitals(Base):
    __tablename__ = "vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blood_pressure = Column(String, nullable=False)   # e.g. "120/80"
    sugar_level = Column(Float, nullable=False)        # mg/dL
    heart_rate = Column(Float, nullable=False)         # bpm
    temperature = Column(Float, nullable=False)        # Celsius
    recorded_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", back_populates="vitals")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)     # e.g. "Twice daily"
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
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.upcoming)

    patient = relationship("User", back_populates="appointments")


class WeeklyReportLog(Base):
    """
    Tracks each weekly email report that was generated/sent - real audit
    trail (also proves the CRUD/side-effect is real, not hardcoded).
    """
    __tablename__ = "weekly_report_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sent_to = Column(String, nullable=False)
    summary_text = Column(Text, nullable=False)
    status = Column(String, default="sent")  # "sent" or "failed"
    sent_at = Column(DateTime, default=datetime.utcnow)

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    relationship_label = Column(String, nullable=False)
    priority = Column(Float, nullable=False)

    patient = relationship("User", back_populates="emergency_contacts")