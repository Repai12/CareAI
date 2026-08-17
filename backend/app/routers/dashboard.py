"""
dashboard.py
------------
MODULE 1 - FEATURE 4 (Member-4 / Repai Ul Islam)
"Patient Health Overview Dashboard — Family and doctor view real-time
summary of latest vitals, medicines, and upcoming appointments."

Design:
- GET /dashboard/{patient_id}
  - Only accessible to the patient themselves, or a family/doctor user who
    has a PatientLink to that patient (real relational access control,
    not hardcoded).
  - Pulls the MOST RECENT vitals row, all ACTIVE medications, and all
    UPCOMING appointments for that patient - all live DB queries.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserRole, Vitals, Medication, Appointment, AppointmentStatus, PatientLink
from app.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    """Access control: patient viewing themselves, OR a linked family/doctor."""
    if current_user.role == UserRole.patient:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own dashboard")
        return

    # family / doctor - must have an explicit link to this patient
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's dashboard")


@router.get("/{patient_id}", response_model=DashboardResponse)
def get_patient_dashboard(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    _assert_can_view(patient_id, current_user, db)

    latest_vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(desc(Vitals.recorded_at))
        .first()
    )

    active_medications = (
        db.query(Medication)
        .filter(Medication.patient_id == patient_id, Medication.active == True)  # noqa: E712
        .all()
    )

    upcoming_appointments = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.upcoming,
        )
        .order_by(Appointment.scheduled_at)
        .all()
    )

    return DashboardResponse(
        patient=patient,
        latest_vitals=latest_vitals,
        active_medications=active_medications,
        upcoming_appointments=upcoming_appointments,
    )
