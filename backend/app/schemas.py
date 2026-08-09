"""
schemas.py
----------
Pydantic models define the shape of JSON going in/out of the API.
Separate from `models.py` (which is the DB shape) - this is standard
FastAPI practice and something you should be able to explain live:
"models.py = database table, schemas.py = API contract".
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

    class Config:
        from_attributes = True


class VitalsOut(BaseModel):
    id: uuid.UUID
    blood_pressure: str
    sugar_level: float
    heart_rate: float
    temperature: float
    recorded_at: datetime

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
    """
    This is the exact shape of Module 1 / Feature 4:
    'real-time summary of latest vitals, medicines, and upcoming appointments'
    """
    patient: UserBase
    latest_vitals: Optional[VitalsOut]
    active_medications: List[MedicationOut]
    upcoming_appointments: List[AppointmentOut]


class WeeklyReportOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    sent_to: str
    summary_text: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True


class TriggerReportRequest(BaseModel):
    patient_id: uuid.UUID
