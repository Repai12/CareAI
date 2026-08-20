"""
models/medication.py
----------------------
OWNED BY MEMBER 2 (Afifa) - Medication Management, Appointments & Prescriptions.

Updated to match Afifa's applied Alembic migration (5c905c544fa2), which
intentionally dropped patient_id/name/schedule_time/active from medications
and patient_id/scheduled_at from appointments in favor of medicine_name +
start_date/end_date, and patient_name/patient_email + appointment_date/
start_time/end_time/reason/google_event_id respectively. The live shared DB
already has this shape - these classes previously still described the old
pre-migration shape, which crashed every query against these tables.

`patient_id` was re-added to Medication (migration 56b76de96e84) because
dropping it entirely left medications with no owner at all - there was no
way to know whose medication a row was, so the dashboard's "active
medications" and the medications router could only ever return an empty
list or every patient's medications mixed together. Appointments keeps its
original patient_email-based linking (not a regression - that's how it
already scoped correctly to a patient's dashboard) rather than churning
it to patient_id too.

MedicationLog (adherence tracker, README S8.4) and VisitNote (doctor
visit history/prescriptions, README S8.3) were added in migration
23cef9385926 - both existed only as dead routers (app/medication_logs.py,
app/visit_notes.py, never registered in main.py) referencing model
classes that were never actually defined anywhere, so neither could have
worked even if wired in.
"""

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Column, String, Date, Time, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
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


class MedicationLogStatus(str, enum.Enum):
    pending = "pending"
    taken = "taken"
    missed = "missed"


class MedicationLog(Base):
    """
    One row per scheduled dose (README S8.4). patient_id is denormalized
    here (also reachable via medication_id -> medications.patient_id)
    so permission checks don't need an extra join - same pattern as
    DietLog in models/vitals.py.
    """
    __tablename__ = "medication_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False)
    taken_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default=MedicationLogStatus.pending.value)


class VisitNote(Base):
    """
    Doctor visit note / prescription (README S8.3). doctor_id is who
    wrote it - needed so a doctor can edit/archive their own notes but
    not another doctor's if a patient has more than one (S8.3's explicit
    rule). patient_name/doctor_name are denormalized snapshots for
    display, same pattern Appointment already uses; patient_id/doctor_id
    are what permission checks actually run against.
    """
    __tablename__ = "visit_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    doctor_name = Column(String, nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    visit_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=False)
    prescription = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | archived
    # AI Prescription Summarizer (README Features table) - cached plain-
    # English explanation, generated on demand, not on every write.
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
