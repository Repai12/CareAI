"""
routers/medications.py
------------------------
OWNED BY MEMBER 2 (Afifa) - Medication Management, Appointment Booking +
Google Calendar Sync, Prescriptions, Adherence Tracking.

Build your endpoints here, e.g.:
    POST /api/v1/medications
    PUT  /api/v1/medications/{id}
    POST /api/v1/appointments/book
    POST /api/v1/medications/{id}/adherence
    GET  /api/v1/prescriptions

The Medication and Appointment tables already exist in
app/models/medication.py (built by Member 4 as a working placeholder so
the Dashboard has real data) - extend those models freely for your
adherence/prescription fields.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/medications", tags=["medications"])

# Add your endpoints below.
