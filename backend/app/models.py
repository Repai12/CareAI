from sqlalchemy import (
    Column,
    String,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from .database import Base


# ============================================================
# MEDICATION
# ============================================================

class Medication(Base):
    __tablename__ = "medications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )

    medicine_name = Column(
        String,
        nullable=False
    )

    dosage = Column(
        String,
        nullable=False
    )

    frequency = Column(
        String,
        nullable=False
    )

    start_date = Column(Date)

    end_date = Column(Date)


# ============================================================
# APPOINTMENT
# ============================================================

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True
    )

    patient_name = Column(
        String,
        nullable=False
    )

    patient_email = Column(
        String,
        nullable=False
    )

    doctor_name = Column(
        String,
        nullable=False
    )

    appointment_date = Column(
        Date,
        nullable=False
    )

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    reason = Column(
        String,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="booked"
    )

    google_event_id = Column(
        String,
        nullable=True
    )


# ============================================================
# MEDICATION REMINDER & ADHERENCE TRACKER
# ============================================================

class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(
        # This can remain INTEGER unless your NeonDB
        # medication_logs.id is also UUID.
        # We will verify this later.
        __import__("sqlalchemy").Integer,
        primary_key=True,
        index=True
    )

    medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id"),
        nullable=False
    )

    scheduled_at = Column(
        DateTime,
        nullable=False
    )

    taken_at = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="pending"
    )


# ============================================================
# DOCTOR VISIT HISTORY & PRESCRIPTION NOTES
# ============================================================

class VisitNote(Base):
    __tablename__ = "visit_notes"

    id = Column(
        __import__("sqlalchemy").Integer,
        primary_key=True,
        index=True
    )

    patient_name = Column(
        String,
        nullable=False
    )

    doctor_name = Column(
        String,
        nullable=False
    )

    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id"),
        nullable=True
    )

    visit_date = Column(
        Date,
        nullable=False
    )

    notes = Column(
        Text,
        nullable=False
    )

    prescription = Column(
        Text,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="active"
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        nullable=False
    )
