from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from . import models
from . import schemas

from .calendar import (
    create_google_calendar_event,
    update_google_calendar_event,
    delete_google_calendar_event
)


# ============================================================
# BANGLADESH TIMEZONE
# ============================================================

BANGLADESH_TZ = timezone(timedelta(hours=6))


def get_current_bangladesh_time():
    """
    Returns the current date/time in Bangladesh.
    """
    return datetime.now(BANGLADESH_TZ)


# ============================================================
# MEDICATION CRUD
# ============================================================

def create_medication(
    db: Session,
    medication: schemas.MedicationCreate
):
    db_medication = models.Medication(
        medicine_name=medication.medicine_name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        start_date=medication.start_date,
        end_date=medication.end_date
    )

    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)

    return db_medication


def get_medications(
    db: Session
):
    return (
        db.query(models.Medication)
        .all()
    )


def get_medication(
    db: Session,
    medication_id: UUID
):
    return (
        db.query(models.Medication)
        .filter(
            models.Medication.id == medication_id
        )
        .first()
    )


def delete_medication(
    db: Session,
    medication_id: UUID
):
    medication = get_medication(
        db,
        medication_id
    )

    if medication:
        db.delete(medication)
        db.commit()

    return medication


def update_medication(
    db: Session,
    medication_id: UUID,
    medication: schemas.MedicationCreate
):
    db_medication = get_medication(
        db,
        medication_id
    )

    if db_medication is None:
        return None

    db_medication.medicine_name = (
        medication.medicine_name
    )

    db_medication.dosage = (
        medication.dosage
    )

    db_medication.frequency = (
        medication.frequency
    )

    db_medication.start_date = (
        medication.start_date
    )

    db_medication.end_date = (
        medication.end_date
    )

    db.commit()
    db.refresh(db_medication)

    return db_medication


# ============================================================
# APPOINTMENT CRUD
# ============================================================

def create_appointment(
    db: Session,
    appointment: schemas.AppointmentCreate
):
    # ========================================================
    # 1. VALIDATE APPOINTMENT TIME
    # ========================================================

    current_time = get_current_bangladesh_time()

    appointment_start = datetime.combine(
        appointment.appointment_date,
        appointment.start_time
    ).replace(
        tzinfo=BANGLADESH_TZ
    )

    appointment_end = datetime.combine(
        appointment.appointment_date,
        appointment.end_time
    ).replace(
        tzinfo=BANGLADESH_TZ
    )

    # Appointment cannot be in the past
    if appointment_start <= current_time:
        raise ValueError(
            "Appointment date and time cannot be in the past."
        )

    # End time must be after start time
    if appointment_end <= appointment_start:
        raise ValueError(
            "Appointment end time must be after start time."
        )

    # ========================================================
    # 2. CREATE APPOINTMENT IN POSTGRESQL
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
    # 3. PREPARE GOOGLE CALENDAR DATETIME
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
    # 4. CREATE GOOGLE CALENDAR EVENT (best-effort)
    # ========================================================
    #
    # Calendar sync is a convenience layer on top of the booking, not a
    # dependency for it (README S7.2's explicit corner case) - the
    # appointment above is already committed and is the source of truth
    # regardless of what happens here. Previously this deleted the
    # just-created appointment and raised on ANY Calendar failure,
    # including simply not having gone through Google's OAuth flow yet
    # (which nobody on the team has, since there's no credentials.json/
    # token.json in this repo) - meaning appointment booking was 100%
    # broken for everyone, not just degraded when Calendar was
    # unavailable. Failures are logged and swallowed instead;
    # google_event_id stays null until a sync succeeds.

    try:
        google_event = create_google_calendar_event(
            title=(
                f"Medical Appointment - "
                f"{appointment.doctor_name}"
            ),
            start_time=start_datetime,
            end_time=end_datetime,
            description=(
                f"Patient: "
                f"{appointment.patient_name}\n"
                f"Email: "
                f"{appointment.patient_email}\n"
                f"Reason: "
                f"{appointment.reason or 'Not specified'}"
            ),
            location=appointment.location
        )
        db_appointment.google_event_id = google_event.get("id")
        db.commit()
        db.refresh(db_appointment)
    except Exception as e:
        print(f"[appointments] Google Calendar sync skipped for {db_appointment.id}: {e}")

    return db_appointment


def get_appointments(
    db: Session
):
    return (
        db.query(models.Appointment)
        .all()
    )


def get_appointment(
    db: Session,
    appointment_id: UUID
):
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id
        )
        .first()
    )


def update_appointment(
    db: Session,
    appointment_id: UUID,
    appointment: schemas.AppointmentCreate
):
    # ========================================================
    # 1. FIND EXISTING APPOINTMENT
    # ========================================================

    db_appointment = get_appointment(
        db,
        appointment_id
    )

    if db_appointment is None:
        return None

    # ========================================================
    # 2. VALIDATE NEW APPOINTMENT TIME
    # ========================================================

    current_time = get_current_bangladesh_time()

    appointment_start = datetime.combine(
        appointment.appointment_date,
        appointment.start_time
    ).replace(
        tzinfo=BANGLADESH_TZ
    )

    appointment_end = datetime.combine(
        appointment.appointment_date,
        appointment.end_time
    ).replace(
        tzinfo=BANGLADESH_TZ
    )

    if appointment_start <= current_time:
        raise ValueError(
            "Appointment date and time cannot be in the past."
        )

    if appointment_end <= appointment_start:
        raise ValueError(
            "Appointment end time must be after start time."
        )

    # ========================================================
    # 3. UPDATE POSTGRESQL
    # ========================================================

    db_appointment.patient_name = (
        appointment.patient_name
    )

    db_appointment.patient_email = (
        appointment.patient_email
    )

    db_appointment.doctor_name = (
        appointment.doctor_name
    )

    db_appointment.appointment_date = (
        appointment.appointment_date
    )

    db_appointment.start_time = (
        appointment.start_time
    )

    db_appointment.end_time = (
        appointment.end_time
    )

    db_appointment.reason = (
        appointment.reason
    )

    db_appointment.location = (
        appointment.location
    )

    db.commit()
    db.refresh(db_appointment)

    # ========================================================
    # 4. UPDATE GOOGLE CALENDAR (best-effort - see create_appointment)
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

        try:

            update_google_calendar_event(
                event_id=(
                    db_appointment.google_event_id
                ),

                title=(
                    f"Medical Appointment - "
                    f"{appointment.doctor_name}"
                ),

                start_time=start_datetime,

                end_time=end_datetime,

                description=(
                    f"Patient: "
                    f"{appointment.patient_name}\n"

                    f"Email: "
                    f"{appointment.patient_email}\n"

                    f"Reason: "
                    f"{appointment.reason or 'Not specified'}"
                ),

                location=appointment.location
            )

        except Exception as e:
            print(f"[appointments] Google Calendar update skipped for {db_appointment.id}: {e}")

    return db_appointment


def delete_appointment(
    db: Session,
    appointment_id: UUID
):
    # ========================================================
    # 1. FIND APPOINTMENT
    # ========================================================

    db_appointment = get_appointment(
        db,
        appointment_id
    )

    if db_appointment is None:
        return None

    # ========================================================
    # 2. GET GOOGLE EVENT ID
    # ========================================================

    google_event_id = (
        db_appointment.google_event_id
    )

    # ========================================================
    # 3. DELETE GOOGLE CALENDAR EVENT (best-effort - see create_appointment)
    # ========================================================

    if google_event_id:

        try:

            delete_google_calendar_event(
                google_event_id
            )

        except Exception as e:
            print(f"[appointments] Google Calendar deletion skipped for {appointment_id}: {e}")

    # ========================================================
    # 4. DELETE FROM POSTGRESQL
    # ========================================================

    db.delete(db_appointment)
    db.commit()

    return db_appointment


# ============================================================
# MEDICATION REMINDER / ADHERENCE + DOCTOR VISIT NOTES
# ============================================================
#
# Both used to have functions here, but nothing ever called them - the
# dead app/medication_logs.py and app/visit_notes.py routers had their
# own separate, more complete inline implementations instead (duplicate
# validation logic, diverging from these). Now that those routers have
# been rewritten with real auth (see app/medication_logs.py,
# app/visit_notes.py), the versions here were just unused dead code
# referencing models.MedicationLog/models.VisitNote, which didn't even
# exist as real tables until this same pass - removed rather than kept
# as a second, unused implementation of the same feature.