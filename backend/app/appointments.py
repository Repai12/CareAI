from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from . import crud
from . import schemas


# ============================================================
# APPOINTMENT ROUTER
# ============================================================

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


# ============================================================
# CREATE APPOINTMENT
# ============================================================

@router.post(
    "/",
    response_model=schemas.AppointmentResponse
)
def add_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
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
# GET ALL APPOINTMENTS
# ============================================================

@router.get(
    "/",
    response_model=list[schemas.AppointmentResponse]
)
def read_appointments(
    db: Session = Depends(get_db)
):
    return crud.get_appointments(db)


# ============================================================
# GET ONE APPOINTMENT
# ============================================================

@router.get(
    "/{appointment_id}",
    response_model=schemas.AppointmentResponse
)
def read_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )