from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# ============================================================
# MEDICATION SCHEMAS
# ============================================================

class MedicationBase(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: date


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(MedicationBase):
    pass


class MedicationResponse(MedicationBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# APPOINTMENT SCHEMAS
# ============================================================

class AppointmentBase(BaseModel):
    patient_name: str
    patient_email: EmailStr
    doctor_name: str
    appointment_date: date
    start_time: time
    end_time: time
    reason: str
    location: str


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(AppointmentBase):
    pass


class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    google_event_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# VISIT NOTE SCHEMAS
# ============================================================

class VisitNoteBase(BaseModel):
    patient_name: str
    doctor_name: str
    visit_date: date
    diagnosis: Optional[str] = None
    consultation_notes: Optional[str] = None
    attachment_url: Optional[str] = None


class VisitNoteCreate(VisitNoteBase):
    pass


class VisitNoteUpdate(VisitNoteBase):
    pass


class VisitNoteResponse(VisitNoteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEDICATION LOG / ADHERENCE SCHEMAS
# ============================================================

class MedicationLogBase(BaseModel):
    medication_id: UUID
    taken_at: Optional[date] = None
    status: Optional[str] = None


class MedicationLogCreate(MedicationLogBase):
    pass


class MedicationLogResponse(MedicationLogBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class MedicationAdherenceResponse(BaseModel):
    medication_id: UUID
    adherence_percentage: float

    model_config = ConfigDict(from_attributes=True)