from datetime import date, time, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment

from .calendar import (
    create_google_calendar_event,
    update_google_calendar_event,
    delete_google_calendar_event
)


router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class AppointmentCreate(BaseModel):
    patient_name: str
    patient_email: EmailStr
    doctor_name: str

    appointment_date: date
    start_time: time
    end_time: time

    reason: str
    location: str


class AppointmentResponse(BaseModel):
    id: int

    patient_name: str
    patient_email: str
    doctor_name: str

    appointment_date: date
    start_time: time
    end_time: time

    reason: str
    location: str

    status: str
    google_event_id: str | None = None

    class Config:
        from_attributes = True


# ============================================================
# HELPER — CREATE DATETIME FOR GOOGLE CALENDAR
# ============================================================

def make_calendar_datetime(
    appointment_date: date,
    appointment_time: time
) -> str:

    dt = datetime.combine(
        appointment_date,
        appointment_time
    )

    return dt.isoformat()


# ============================================================
# GET ALL APPOINTMENTS
# ============================================================

@router.get(
    "/",
    response_model=list[AppointmentResponse]
)
def get_appointments(
    db: Session = Depends(get_db)
):

    appointments = (
        db.query(Appointment)
        .order_by(
            Appointment.appointment_date,
            Appointment.start_time
        )
        .all()
    )

    return appointments


# ============================================================
# GET SINGLE APPOINTMENT
# ============================================================

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id
        )
        .first()
    )

    if appointment is None:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found."
        )

    return appointment


# ============================================================
# CREATE APPOINTMENT
# ============================================================

@router.post(
    "/",
    response_model=AppointmentResponse
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate time
    # --------------------------------------------------------

    if (
        appointment_data.end_time
        <= appointment_data.start_time
    ):

        raise HTTPException(
            status_code=400,
            detail="End time must be later than start time."
        )


    # --------------------------------------------------------
    # Check conflicting appointments
    # --------------------------------------------------------

    existing_appointments = (
        db.query(Appointment)
        .filter(
            Appointment.appointment_date
            == appointment_data.appointment_date
        )
        .all()
    )


    for existing in existing_appointments:

        if existing.status == "cancelled":
            continue

        if (
            appointment_data.start_time
            < existing.end_time
            and
            appointment_data.end_time
            > existing.start_time
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "This appointment time conflicts "
                    "with an existing appointment."
                )
            )


    # --------------------------------------------------------
    # Create database appointment
    # --------------------------------------------------------

    new_appointment = Appointment(

        patient_name=
            appointment_data.patient_name,

        patient_email=
            appointment_data.patient_email,

        doctor_name=
            appointment_data.doctor_name,

        appointment_date=
            appointment_data.appointment_date,

        start_time=
            appointment_data.start_time,

        end_time=
            appointment_data.end_time,

        reason=
            appointment_data.reason,

        location=
            appointment_data.location,

        status="booked",

        google_event_id=None
    )


    db.add(new_appointment)

    db.commit()

    db.refresh(new_appointment)


    # --------------------------------------------------------
    # CREATE GOOGLE CALENDAR EVENT
    # --------------------------------------------------------

    try:

        calendar_event = create_google_calendar_event(

            title=(
                f"Appointment with "
                f"{new_appointment.doctor_name}"
            ),

            start_time=make_calendar_datetime(
                new_appointment.appointment_date,
                new_appointment.start_time
            ),

            end_time=make_calendar_datetime(
                new_appointment.appointment_date,
                new_appointment.end_time
            ),

            description=(
                f"Patient: "
                f"{new_appointment.patient_name}\n"
                f"Email: "
                f"{new_appointment.patient_email}\n"
                f"Reason: "
                f"{new_appointment.reason}"
            ),

            location=
                new_appointment.location
        )


        # Save Google Calendar event ID
        new_appointment.google_event_id = (
            calendar_event.get("id")
        )

        db.commit()

        db.refresh(new_appointment)


    except Exception as e:

        # The appointment remains in PostgreSQL,
        # but the Calendar event could not be created.

        print(
            "Google Calendar event creation failed:",
            str(e)
        )


    return new_appointment


# ============================================================
# UPDATE APPOINTMENT
# ============================================================

@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db)
):

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id
        )
        .first()
    )


    if appointment is None:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found."
        )


    # --------------------------------------------------------
    # Validate time
    # --------------------------------------------------------

    if (
        appointment_data.end_time
        <= appointment_data.start_time
    ):

        raise HTTPException(
            status_code=400,
            detail="End time must be later than start time."
        )


    # --------------------------------------------------------
    # Update database fields
    # --------------------------------------------------------

    appointment.patient_name = (
        appointment_data.patient_name
    )

    appointment.patient_email = (
        appointment_data.patient_email
    )

    appointment.doctor_name = (
        appointment_data.doctor_name
    )

    appointment.appointment_date = (
        appointment_data.appointment_date
    )

    appointment.start_time = (
        appointment_data.start_time
    )

    appointment.end_time = (
        appointment_data.end_time
    )

    appointment.reason = (
        appointment_data.reason
    )

    appointment.location = (
        appointment_data.location
    )


    db.commit()

    db.refresh(appointment)


    # --------------------------------------------------------
    # UPDATE GOOGLE CALENDAR EVENT
    # --------------------------------------------------------

    if appointment.google_event_id:

        try:

            update_google_calendar_event(

                event_id=
                    appointment.google_event_id,

                title=(
                    f"Appointment with "
                    f"{appointment.doctor_name}"
                ),

                start_time=make_calendar_datetime(
                    appointment.appointment_date,
                    appointment.start_time
                ),

                end_time=make_calendar_datetime(
                    appointment.appointment_date,
                    appointment.end_time
                ),

                description=(
                    f"Patient: "
                    f"{appointment.patient_name}\n"
                    f"Email: "
                    f"{appointment.patient_email}\n"
                    f"Reason: "
                    f"{appointment.reason}"
                ),

                location=
                    appointment.location
            )

        except Exception as e:

            print(
                "Google Calendar event update failed:",
                str(e)
            )


    return appointment


# ============================================================
# DELETE / CANCEL APPOINTMENT
# ============================================================

@router.delete(
    "/{appointment_id}"
)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id
        )
        .first()
    )


    if appointment is None:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found."
        )


    # --------------------------------------------------------
    # DELETE GOOGLE CALENDAR EVENT
    # --------------------------------------------------------

    if appointment.google_event_id:

        try:

            delete_google_calendar_event(
                appointment.google_event_id
            )

        except Exception as e:

            print(
                "Google Calendar event deletion failed:",
                str(e)
            )


    # --------------------------------------------------------
    # CANCEL DATABASE APPOINTMENT
    # --------------------------------------------------------

    appointment.status = "cancelled"

    db.commit()


    return {
        "message":
            "Appointment cancelled successfully."
    }