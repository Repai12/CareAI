"""
routers/dashboard.py
----------------------
OWNED BY MEMBER 4 (Repai) - Module 1, Feature 4: Patient Health Overview
Dashboard.

Runs the three data-source queries in parallel using asyncio.gather(),
each in its own short-lived DB session (a SQLAlchemy Session isn't safe to
share across concurrent threads, so each parallel query gets its own).
"""

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from anyio import to_thread

from app.database import get_db, SessionLocal
from app.auth import get_current_user
from app.models.user import User, UserRole, PatientLink
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment, AppointmentStatus
from app.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own dashboard")
        return

    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's dashboard")


def _fetch_latest_vitals(patient_id: uuid.UUID):
    db = SessionLocal()
    try:
        return (
            db.query(VitalsLog)
            .filter(VitalsLog.patient_id == patient_id)
            .order_by(desc(VitalsLog.logged_at))
            .first()
        )
    finally:
        db.close()


def _fetch_active_medications(patient_id: uuid.UUID):
    db = SessionLocal()
    try:
        return (
            db.query(Medication)
            .filter(Medication.patient_id == patient_id, Medication.active == True)  # noqa: E712
            .all()
        )
    finally:
        db.close()


def _fetch_upcoming_appointments(patient_id: uuid.UUID):
    db = SessionLocal()
    try:
        return (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.status == AppointmentStatus.upcoming.value,
            )
            .order_by(Appointment.scheduled_at)
            .limit(3)  # "next 3 upcoming appointments" per spec
            .all()
        )
    finally:
        db.close()


@router.get("/{patient_id}", response_model=DashboardResponse)
async def get_patient_dashboard(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise HTTPException(404, "Patient not found")

    _assert_can_view(patient_id, current_user, db)

    # Parallel, non-blocking fetch of the three data sources - each runs
    # in its own thread with its own DB session.
    latest_vitals, active_medications, upcoming_appointments = await asyncio.gather(
        to_thread.run_sync(_fetch_latest_vitals, patient_id),
        to_thread.run_sync(_fetch_active_medications, patient_id),
        to_thread.run_sync(_fetch_upcoming_appointments, patient_id),
    )

    return DashboardResponse(
        patient=patient,
        latest_vitals=latest_vitals,
        active_medications=active_medications,
        upcoming_appointments=upcoming_appointments,
    )
