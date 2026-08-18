from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .models.user import User, UserRole, PatientLink
from . import crud
from . import schemas


# ============================================================
# APPOINTMENT ROUTER
# ============================================================

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


def _find_patient_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email, User.role == UserRole.patient.value).first()


def _assert_can_view_by_email(patient_email: str, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.email != patient_email:
            raise HTTPException(403, "Patients can only view their own appointments")
        return
    patient = _find_patient_by_email(db, patient_email)
    if not patient:
        raise HTTPException(404, "Patient not found")
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient.id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's appointments")


def _assert_can_edit_by_email(patient_email: str, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.email != patient_email:
            raise HTTPException(403, "Patients can only manage their own appointments")
        return
    if current_user.role == UserRole.doctor.value:
        patient = _find_patient_by_email(db, patient_email)
        if not patient:
            raise HTTPException(404, "Patient not found")
        link = (
            db.query(PatientLink)
            .filter(PatientLink.patient_id == patient.id, PatientLink.viewer_id == current_user.id)
            .first()
        )
        if not link:
            raise HTTPException(403, "You are not linked to this patient")
        return
    raise HTTPException(403, "Family members can view appointments but not book, edit, or cancel them")


# ============================================================
# CREATE APPOINTMENT
# ============================================================

@router.post(
    "/",
    response_model=schemas.AppointmentResponse
)
def add_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_edit_by_email(appointment.patient_email, current_user, db)
    try:
        return crud.create_appointment(
            db,
            appointment
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET APPOINTMENTS FOR A SPECIFIC PATIENT
# ============================================================

@router.get(
    "/patient/{patient_id}",
    response_model=list[schemas.AppointmentResponse]
)
def read_appointments_for_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    _assert_can_view_by_email(patient.email, current_user, db)
    return crud.get_appointments(db, patient.email)


# ============================================================
# GET ONE APPOINTMENT
# ============================================================

@router.get(
    "/{appointment_id}",
    response_model=schemas.AppointmentResponse
)
def read_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = crud.get_appointment(
        db,
        appointment_id
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    _assert_can_view_by_email(appointment.patient_email, current_user, db)

    return appointment


# ============================================================
# UPDATE APPOINTMENT
# ============================================================

@router.put(
    "/{appointment_id}",
    response_model=schemas.AppointmentResponse
)
def edit_appointment(
    appointment_id: UUID,
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = crud.get_appointment(db, appointment_id)
    if existing is None:
        raise HTTPException(404, "Appointment not found")
    _assert_can_edit_by_email(existing.patient_email, current_user, db)

    try:
        updated = crud.update_appointment(
            db,
            appointment_id,
            appointment
        )

        if updated is None:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        return updated

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE APPOINTMENT
# ============================================================

@router.delete(
    "/{appointment_id}"
)
def remove_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = crud.get_appointment(db, appointment_id)
    if existing is None:
        raise HTTPException(404, "Appointment not found")
    _assert_can_edit_by_email(existing.patient_email, current_user, db)

    try:
        appointment = crud.delete_appointment(
            db,
            appointment_id
        )

        if appointment is None:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        return {
            "message": "Appointment deleted successfully"
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
