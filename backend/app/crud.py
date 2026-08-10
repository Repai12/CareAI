from sqlalchemy.orm import Session
from . import models
from . import schemas
from .calendar import (
    create_google_calendar_event,
    update_google_calendar_event,
    delete_google_calendar_event
)

def create_medication(db: Session, medication: schemas.MedicationCreate):
    db_medication = models.Medication(**medication.model_dump())

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)

    return db_medication


def get_medications(db: Session):
    return db.query(models.Medication).all()


def get_medication(db: Session, medication_id: int):
    return (
        db.query(models.Medication)
        .filter(models.Medication.id == medication_id)
        .first()
    )


def delete_medication(db: Session, medication_id: int):
    medication = get_medication(db, medication_id)

    if medication:
        db.delete(medication)
        db.commit()

    return medication
def update_medication(db: Session, medication_id: int, medication: schemas.MedicationCreate):
    db_medication = get_medication(db, medication_id)

    if db_medication is None:
        return None

    db_medication.medicine_name = medication.medicine_name
    db_medication.dosage = medication.dosage
    db_medication.frequency = medication.frequency
    db_medication.start_date = medication.start_date
    db_medication.end_date = medication.end_date

    db.commit()
    db.refresh(db_medication)

    return db_medication
def create_appointment(
    db: Session,
    appointment: schemas.AppointmentCreate
):
    # ========================================================
    # 1. Create the appointment in PostgreSQL
    # ========================================================

    db_appointment = models.Appointment(
        patient_name=appointment.patient_name,
        patient_email=appointment.patient_email,
        doctor_name=appointment.doctor_name,
        appointment_date=appointment.appointment_date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        reason=appointment.reason,
        location=appointment.location,
        status="booked"
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # ========================================================
    # 2. Prepare date and time for Google Calendar
    # ========================================================

    start_datetime = (
        f"{appointment.appointment_date}T"
        f"{appointment.start_time}+06:00"
    )

    end_datetime = (
        f"{appointment.appointment_date}T"
        f"{appointment.end_time}+06:00"
    )

    # ========================================================
    # 3. Create the appointment in Google Calendar
    # ========================================================

    try:

        google_event = create_google_calendar_event(
            title=(
                f"Medical Appointment - "
                f"{appointment.doctor_name}"
            ),
            start_time=start_datetime,
            end_time=end_datetime,
            description=(
                f"Patient: {appointment.patient_name}\n"
                f"Email: {appointment.patient_email}\n"
                f"Reason: {appointment.reason}"
            ),
            location=appointment.location
        )

        # ====================================================
        # 4. Save Google's event ID in PostgreSQL
        # ====================================================

        db_appointment.google_event_id = google_event.get("id")

        db.commit()
        db.refresh(db_appointment)

    except Exception as e:

        # If Google Calendar fails, remove the appointment
        # that was just created in PostgreSQL.

        db.delete(db_appointment)
        db.commit()

        raise Exception(
            f"Appointment could not be synchronized "
            f"with Google Calendar: {str(e)}"
        )

    # ========================================================
    # 5. Return the completed appointment
    # ========================================================

    return db_appointment


def get_appointments(db: Session):
    return db.query(models.Appointment).all()


def get_appointment(db: Session, appointment_id: int):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )


def update_appointment(
    db: Session,
    appointment_id: int,
    appointment: schemas.AppointmentCreate
):
    # ========================================================
    # 1. Find the existing appointment
    # ========================================================

    db_appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id
        )
        .first()
    )

    if db_appointment is None:
        return None

    # ========================================================
    # 2. Update the appointment in PostgreSQL
    # ========================================================

    db_appointment.patient_name = appointment.patient_name
    db_appointment.patient_email = appointment.patient_email
    db_appointment.doctor_name = appointment.doctor_name
    db_appointment.appointment_date = appointment.appointment_date
    db_appointment.start_time = appointment.start_time
    db_appointment.end_time = appointment.end_time
    db_appointment.reason = appointment.reason
    db_appointment.location = appointment.location

    db.commit()
    db.refresh(db_appointment)

    # ========================================================
    # 3. Check whether this appointment has a Google event
    # ========================================================

    if db_appointment.google_event_id:

        start_datetime = (
            f"{appointment.appointment_date}T"
            f"{appointment.start_time}+06:00"
        )

        end_datetime = (
            f"{appointment.appointment_date}T"
            f"{appointment.end_time}+06:00"
        )

        # ====================================================
        # 4. Update the corresponding Google Calendar event
        # ====================================================

        try:

            update_google_calendar_event(
                event_id=db_appointment.google_event_id,
                title=(
                    f"Medical Appointment - "
                    f"{appointment.doctor_name}"
                ),
                start_time=start_datetime,
                end_time=end_datetime,
                description=(
                    f"Patient: {appointment.patient_name}\n"
                    f"Email: {appointment.patient_email}\n"
                    f"Reason: {appointment.reason}"
                ),
                location=appointment.location
            )

        except Exception as e:

            raise Exception(
                "Appointment was updated in PostgreSQL, "
                "but Google Calendar could not be updated: "
                f"{str(e)}"
            )

    # ========================================================
    # 5. Return the updated appointment
    # ========================================================

    return db_appointment


def delete_appointment(
    db: Session,
    appointment_id: int
):
    # ========================================================
    # 1. Find the appointment
    # ========================================================

    db_appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id
        )
        .first()
    )

    if db_appointment is None:
        return None

    # ========================================================
    # 2. Get the Google Calendar event ID
    # ========================================================

    google_event_id = db_appointment.google_event_id

    # ========================================================
    # 3. Delete the Google Calendar event first
    # ========================================================

    if google_event_id:

        try:

            delete_google_calendar_event(
                google_event_id
            )

        except Exception as e:

            raise Exception(
                "Appointment could not be deleted because "
                "the Google Calendar event could not be "
                f"deleted: {str(e)}"
            )

    # ========================================================
    # 4. Delete appointment from PostgreSQL
    # ========================================================

    db.delete(db_appointment)
    db.commit()

    # ========================================================
    # 5. Return the deleted appointment
    # ========================================================

    return db_appointment