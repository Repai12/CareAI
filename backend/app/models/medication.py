"""
models/medication.py
----------------------
OWNED BY MEMBER 2 (Afifa) - Medication Management, Appointments & Prescriptions.

Base Medication/Appointment shape matches the applied Alembic migration
(5c905c544fa2). MedicationLog and VisitNote (adherence tracking + doctor
visit notes) plus Medication.patient_id (added after the fact - the
migration dropped it entirely, leaving no way to scope a medication to a
specific patient) round out the rest of this module.
"""

import uuid
from datetime import date, time

from sqlalchemy import Column, String, Date, Time, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Nullable because pre-existing rows have no owner; new rows always set it.
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    medicine_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    status = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    patient_email = Column(String, nullable=False)
    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String, nullable=True)
    google_event_id = Column(String, nullable=True)


class MedicationLog(Base):
    """Reminder/adherence tracking."""

    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    taken_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="pending")


class VisitNote(Base):
    """Doctor visit history / prescription notes."""

    __tablename__ = "visit_notes"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    doctor_name = Column(String, nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    visit_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=False)
    prescription = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
