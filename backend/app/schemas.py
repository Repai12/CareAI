"""
schemas.py
----------
API request/response shapes (Pydantic).

Contains shared schemas for:
- Authentication / users
- Vitals
- Dashboard
- Reports
- AI / health features
- Emergency / fall detection
- Member 2: Medications
- Member 2: Appointments
- Member 2: Google Calendar
- Member 2: Medication adherence
- Member 2: Doctor visit history / prescription notes
"""

import uuid
from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# ============================================================
# USER
# ============================================================

class UserBase(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    patient_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# VITALS
# ============================================================

class VitalsOut(BaseModel):
    id: uuid.UUID
    blood_pressure: str
    sugar_level: float
    heart_rate: float
    temperature: float
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VitalsIn(BaseModel):
    blood_pressure: str
    sugar_level: float
    heart_rate: float
    temperature: float
    notes: Optional[str] = None


class VitalsUpdate(BaseModel):
    blood_pressure: Optional[str] = None
    sugar_level: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None


class VitalsEntryOut(BaseModel):
    id: uuid.UUID
    blood_pressure: str
    sugar_level: float
    heart_rate: float
    temperature: float
    notes: Optional[str] = None
    logged_at: datetime
    is_abnormal: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEDICATION — TEAM / DASHBOARD
# ============================================================

class MedicationOut(BaseModel):
    id: uuid.UUID
    name: str
    dosage: str
    frequency: str
    schedule_time: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# APPOINTMENT — TEAM / DASHBOARD
# ============================================================

class AppointmentOut(BaseModel):
    id: uuid.UUID
    doctor_name: str
    scheduled_at: datetime
    location: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DASHBOARD
# ============================================================

class DashboardResponse(BaseModel):
    patient: UserBase
    latest_vitals: Optional[VitalsOut] = None
    active_medications: List[MedicationOut]
    upcoming_appointments: List[AppointmentOut]


# ============================================================
# EMAIL / REPORTS
# ============================================================

class EmailLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    recipient_email: str
    report_type: str
    status: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TriggerReportRequest(BaseModel):
    patient_id: uuid.UUID


# ============================================================
# HEALTH REPORTS
# ============================================================

class HealthReportOut(BaseModel):
    id: uuid.UUID
    filename: str
    ai_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# SYMPTOM CHECKER
# ============================================================

class SymptomCheckIn(BaseModel):
    symptoms: str


class SymptomLogOut(BaseModel):
    id: uuid.UUID
    symptoms: str
    ai_response: str
    urgency: str
    escalated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# DIET ADVISOR
# ============================================================

class DietPlanOut(BaseModel):
    id: uuid.UUID
    based_on_summary: str
    ai_plan: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DietLogIn(BaseModel):
    plan_id: uuid.UUID
    followed: bool
    note: Optional[str] = None


class DietLogOut(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    followed: bool
    note: Optional[str] = None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# EMERGENCY CONTACTS
# ============================================================

class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    relationship: str
    priority: int = 1


class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    priority: Optional[int] = None


class EmergencyContactOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    phone: str
    relationship: str
    priority: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# FALL DETECTION
# ============================================================

class FallIncidentCreate(BaseModel):
    severity: str
    details: Optional[str] = None


class FallIncidentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    severity: str
    details: Optional[str] = None
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEMBER 2 — MEDICATION MANAGEMENT
# ============================================================

class MedicationBase(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: date


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    medicine_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MedicationResponse(MedicationBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEMBER 2 — APPOINTMENTS
# ============================================================

class AppointmentBase(BaseModel):
    patient_name: str
    patient_email: EmailStr
    doctor_name: str
    appointment_date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None
    location: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_email: Optional[EmailStr] = None
    doctor_name: Optional[str] = None
    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: UUID
    status: str
    google_event_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEMBER 2 — GOOGLE CALENDAR
# ============================================================

class CalendarEventResponse(BaseModel):
    appointment_id: UUID
    google_event_id: Optional[str] = None
    message: Optional[str] = None


# ============================================================
# MEMBER 2 — MEDICATION LOG / ADHERENCE
# ============================================================

class MedicationLogBase(BaseModel):
    medication_id: UUID
    scheduled_at: datetime
    taken_at: Optional[datetime] = None
    status: Optional[str] = None


class MedicationLogCreate(BaseModel):
    medication_id: UUID
    scheduled_at: datetime


class MedicationLogResponse(MedicationLogBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class MedicationAdherenceResponse(BaseModel):
    medication_id: UUID
    taken: int = 0
    missed: int = 0
    pending: int = 0
    adherence_percentage: float

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MEMBER 2 — DOCTOR VISIT HISTORY / PRESCRIPTION NOTES
# ============================================================

class VisitNoteBase(BaseModel):
    patient_name: str
    doctor_name: str
    appointment_id: Optional[UUID] = None
    visit_date: date
    notes: str
    prescription: Optional[str] = None


class VisitNoteCreate(VisitNoteBase):
    pass


class VisitNoteUpdate(BaseModel):
    notes: Optional[str] = None
    prescription: Optional[str] = None


class VisitNoteResponse(VisitNoteBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    class Config:
        from_attributes = True

class SafetyCheckinOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    checked_in_at: datetime
    is_checked_in: bool

    class Config:
        from_attributes = True

