from datetime import date, time

from pydantic import BaseModel


class MedicationCreate(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: date


class MedicationResponse(MedicationCreate):
    id: int

    class Config:
        from_attributes = True
class AppointmentCreate(BaseModel):
    patient_name: str
    patient_email: str
    doctor_name: str
    appointment_date: date
    start_time: time
    end_time: time
    reason: str | None = None
    location: str | None = None


class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    patient_email: str
    doctor_name: str
    appointment_date: date
    start_time: time
    end_time: time
    reason: str | None = None
    location: str | None = None
    status: str
    google_event_id: str | None = None

    class Config:
        from_attributes = True