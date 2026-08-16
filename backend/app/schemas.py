"""
schemas.py
----------
API request/response shapes (Pydantic). Add your own schemas here as you
build features, or split into schemas/ if this file gets large - talk to
the team before restructuring since everyone imports from here.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    patient_code: Optional[str] = None

    class Config:
        from_attributes = True


class VitalsOut(BaseModel):
    id: uuid.UUID
    blood_pressure: str
    sugar_level: float
    heart_rate: float
    temperature: float
    logged_at: datetime

    class Config:
        from_attributes = True


class MedicationOut(BaseModel):
    id: uuid.UUID
    name: str
    dosage: str
    frequency: str
    schedule_time: str
    active: bool

    class Config:
        from_attributes = True


class AppointmentOut(BaseModel):
    id: uuid.UUID
    doctor_name: str
    scheduled_at: datetime
    location: Optional[str]
    status: str

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    patient: UserBase
    latest_vitals: Optional[VitalsOut]
    active_medications: List[MedicationOut]
    upcoming_appointments: List[AppointmentOut]


class EmailLogOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    recipient_email: str
    report_type: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True


class TriggerReportRequest(BaseModel):
    patient_id: uuid.UUID



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

    class Config:
        from_attributes = True

class FallIncidentCreate(BaseModel):
    severity: str
    details: Optional[str] = None


class FallIncidentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    severity: str
    details: Optional[str]
    occurred_at: datetime

    class Config:
        from_attributes = True