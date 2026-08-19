"""
appointments.py
------------------
OWNED BY MEMBER 2 (Afifa) - Appointment Booking + Calendar Sync (README
S7.2). Rewritten from the original version, which had NO authentication
at all - GET /appointments/ returned every patient's appointments to
anyone with a valid token, and nothing verified the caller was allowed
to book/edit/cancel a given patient's appointment. Reuses crud.py's
appointment functions (which already have real validation - can't book
in the past, end must be after start - and, as of this pass, treat
Google Calendar sync as best-effort rather than rolling back the
booking on failure), wrapped with the same patient_id + care_link
permission check every other router in the app uses.

patient_name/patient_email are always taken from the patient's own user
record server-side, never from the request body - otherwise a caller
could submit someone else's identity into their own appointment.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from .models.medication import Appointment
from .models.notification import NotificationCategory
from .services.notification_service import create_notification
from . import crud
from . import schemas


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def _assert_can_view(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own appointments")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's appointments")


def _assert_can_manage(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only manage their own appointments")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
            CareLink.permission_level == CareLinkPermission.view_and_manage.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have permission to manage this patient's appointments")


def _get_patient_or_404(patient_id: UUID, db: Session) -> User:
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.get("/{patient_id}", response_model=list[schemas.AppointmentResponse])
def list_appointments(patient_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = _get_patient_or_404(patient_id, db)
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(Appointment)
        .filter(Appointment.patient_email == patient.email)
        .order_by(Appointment.appointment_date, Appointment.start_time)
        .all()
    )


@router.post("/{patient_id}", response_model=schemas.AppointmentResponse)
def book_appointment(
    patient_id: UUID,
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_can_manage(patient_id, current_user, db)

    # Identity always comes from the patient record, never the request body.
    payload = appointment.model_copy(update={"patient_name": patient.name, "patient_email": patient.email})

    try:
        created = crud.create_appointment(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    create_notification(
        db,
        patient_id=patient_id,
        event_type="APPOINTMENT_BOOKED",
        title="Appointment booked",
        message=f"An appointment with {created.doctor_name} was booked for {created.appointment_date}.",
        category=NotificationCategory.appointment,
    )
    return created


@router.get("/{patient_id}/{appointment_id}", response_model=schemas.AppointmentResponse)
def get_appointment(
    patient_id: UUID,
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_can_view(patient_id, current_user, db)

    appt = crud.get_appointment(db, appointment_id)
    if appt is None or appt.patient_email != patient.email:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


@router.put("/{patient_id}/{appointment_id}", response_model=schemas.AppointmentResponse)
def edit_appointment(
    patient_id: UUID,
    appointment_id: UUID,
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_can_manage(patient_id, current_user, db)

    existing = crud.get_appointment(db, appointment_id)
    if existing is None or existing.patient_email != patient.email:
        raise HTTPException(status_code=404, detail="Appointment not found")

    payload = appointment.model_copy(update={"patient_name": patient.name, "patient_email": patient.email})
    try:
        updated = crud.update_appointment(db, appointment_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return updated


@router.delete("/{patient_id}/{appointment_id}")
def remove_appointment(
    patient_id: UUID,
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_can_manage(patient_id, current_user, db)

    existing = crud.get_appointment(db, appointment_id)
    if existing is None or existing.patient_email != patient.email:
        raise HTTPException(status_code=404, detail="Appointment not found")

    doctor_name, appt_date = existing.doctor_name, existing.appointment_date
    crud.delete_appointment(db, appointment_id)

    create_notification(
        db,
        patient_id=patient_id,
        event_type="APPOINTMENT_CANCELLED",
        title="Appointment cancelled",
        message=f"The appointment with {doctor_name} on {appt_date} was cancelled.",
        category=NotificationCategory.appointment,
    )
    return {"message": "Appointment deleted successfully"}
