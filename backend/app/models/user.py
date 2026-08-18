"""
models/user.py
---------------
SHARED FILE - core identity tables used by every feature. Edit with care
and tell the team if you change this.

Linking mechanism: every Patient gets an immutable 8-character
`patient_code` (e.g. CARE-8921) generated at registration. Family members
and doctors register by supplying that code, which creates a row in
PatientLink - this is how the system knows who's allowed to see whose data.
"""

import enum
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

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
    role = Column(String, nullable=False)  # UserRole value

    # Only set for role == patient. Unique, shareable code used by
    # family/doctor accounts to link themselves to this patient.
    patient_code = Column(String, unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    vitals = relationship("VitalsLog", back_populates="patient", cascade="all, delete-orphan")
    # medications/appointments are no longer linked via patient_id (Afifa's
    # migration 5c905c544fa2 replaced that FK with patient_name/patient_email
    # on appointments and dropped it entirely from medications) - no
    # relationship() possible here without a matching FK on the other side.

    emergency_contacts = relationship(
    "EmergencyContact",
    back_populates="user",
    cascade="all, delete-orphan"
)
class PatientLink(Base):
    """
    Connects a family member or doctor account to the patient(s) they can
    view. One row per (patient, viewer) pair - a viewer can be linked to
    multiple patients, a patient can have multiple viewers.
    """
    __tablename__ = "patient_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    viewer_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_label = Column(String, default="family")  # "family" or "doctor"
