"""
models/user.py
---------------
SHARED FILE - core identity tables used by every feature. Edit with care
and tell the team if you change this.

Linking mechanism: every Patient gets an immutable 8-character
`patient_code` (e.g. CARE-8921) generated at registration. Family members
and doctors register by supplying that code, which creates a `care_links`
row - this is how the system knows who's allowed to see whose data.

Every access check elsewhere in the app must require
`CareLink.status == CareLinkStatus.active` - a row merely existing is not
enough. Registering with a patient_code only creates a *pending* link;
the patient has to approve it (see routers/me.py's connection endpoints)
before any data is shared. This two-sided approval is deliberate (README
S4.2/S13): auto-granting access the moment someone types in a code they
found or guessed would let a stranger silently attach themselves to a
patient's medical data.
"""

import enum
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime
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

    # Email-click verification-before-login was removed: with only a
    # single-recipient Resend sandbox account (no verified domain), nobody
    # but the team's own test inbox could ever receive the link, which
    # made it impossible for anyone else (e.g. a grader) to sign up with
    # their own email and get in. Accounts are active immediately on
    # registration now. verification_token/_expires_at are unused leftover
    # columns - kept rather than migrated away since nothing else in the
    # app touches them. Doctors are separately "unverified" in the
    # clinical sense (no license-registry check) regardless of this flag -
    # see UserRole.doctor handling in routers/auth.py.
    is_verified = Column(Boolean, nullable=False, default=True)
    verification_token = Column(String, nullable=True, index=True)
    verification_token_expires_at = Column(DateTime, nullable=True)

    # Password reset (README S3.3) - single-use, invalidated by clearing
    # these columns once redeemed or once a new one is requested.
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

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
class CareLinkStatus(str, enum.Enum):
    pending = "pending"    # created at registration/invite time, not yet usable
    active = "active"      # patient approved - data actually flows now
    declined = "declined"  # patient rejected before it ever became active
    revoked = "revoked"    # was active, patient later revoked it


class CareLinkPermission(str, enum.Enum):
    view_only = "view_only"
    view_and_manage = "view_and_manage"


class CareLink(Base):
    """
    Connects a family member or doctor account to the patient(s) they can
    view. One row per (patient, viewer) pair - a viewer can be linked to
    multiple patients, a patient can have multiple viewers (README S4.1).

    `status` starts at `pending` and only becomes `active` once the
    patient approves (routers/me.py) - every read of a patient's data
    elsewhere in the app must filter on `status == active`, not just on
    the row existing. Rows are never hard-deleted on revoke (only
    `status` flips + `revoked_at` is stamped) so there's an audit trail
    of who had access and when (README S4.4).
    """
    __tablename__ = "care_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    viewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    link_role = Column(String, nullable=False)  # "family" or "doctor" - matches viewer_id's account role
    relationship_label = Column(String, nullable=True)  # free text set at invite time, e.g. "Daughter"
    permission_level = Column(String, nullable=False, default=CareLinkPermission.view_only.value)
    status = Column(String, nullable=False, default=CareLinkStatus.pending.value, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


class RefreshToken(Base):
    """
    One row per issued refresh token (README S3.2/3.4) - lets us revoke a
    single session (logout) or every session for a user ("logout
    everywhere" in /settings) without needing a JWT blacklist. Only the
    SHA-256 hash of the token is stored, never the raw value, so a DB leak
    doesn't hand out working refresh tokens.
    """
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
