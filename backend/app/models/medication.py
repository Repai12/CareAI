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
"""

import uuid
from datetime import date, time

from sqlalchemy import Column, String, Date, Time
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
