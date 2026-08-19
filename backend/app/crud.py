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
# MEDICATION REMINDER / ADHERENCE
# ============================================================

def create_medication_log(
    db: Session,
    medication_log: schemas.MedicationLogCreate
):
    # Make sure medication exists
    medication = get_medication(
        db,
        medication_log.medication_id
    )

    if medication is None:
        raise ValueError(
            "Medication not found."
        )

    # Prevent creating a reminder in the past
    current_time = get_current_bangladesh_time()

    scheduled_time = medication_log.scheduled_at

    if scheduled_time.tzinfo is None:
        scheduled_time = scheduled_time.replace(
            tzinfo=BANGLADESH_TZ
        )

    if scheduled_time <= current_time:
        raise ValueError(
            "Medication reminder time cannot be in the past."
        )

    db_log = models.MedicationLog(
        medication_id=medication_log.medication_id,
        scheduled_at=medication_log.scheduled_at,
        status="pending"
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return db_log


def get_medication_logs(
    db: Session,
    medication_id: UUID
):
    return (
        db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.medication_id
            == medication_id
        )
        .order_by(
            models.MedicationLog.scheduled_at
        )
        .all()
    )


def mark_medication_taken(
    db: Session,
    log_id: int
):
    db_log = (
        db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.id == log_id
        )
        .first()
    )

    if db_log is None:
        return None

    db_log.taken_at = (
        get_current_bangladesh_time()
    )

    db_log.status = "taken"

    db.commit()
    db.refresh(db_log)

    return db_log


def mark_medication_missed(
    db: Session,
    log_id: int
):
    db_log = (
        db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.id == log_id
        )
        .first()
    )

    if db_log is None:
        return None

    db_log.status = "missed"

    db.commit()
    db.refresh(db_log)

    return db_log


def get_medication_adherence(
    db: Session,
    medication_id: UUID
):
    logs = (
        db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.medication_id
            == medication_id
        )
        .all()
    )

    taken = sum(
        1 for log in logs
        if log.status == "taken"
    )

    missed = sum(
        1 for log in logs
        if log.status == "missed"
    )

    pending = sum(
        1 for log in logs
        if log.status == "pending"
    )

    completed = taken + missed

    if completed == 0:
        adherence_percentage = 0.0
    else:
        adherence_percentage = (
            taken / completed
        ) * 100

    return {
        "medication_id": medication_id,
        "taken": taken,
        "missed": missed,
        "pending": pending,
        "adherence_percentage": round(
            adherence_percentage,
            2
        )
    }


# ============================================================
# DOCTOR VISIT HISTORY / PRESCRIPTION NOTES
# ============================================================

def create_visit_note(
    db: Session,
    visit_note: schemas.VisitNoteCreate
):
    # ========================================================
    # CHECK APPOINTMENT IF PROVIDED
    # ========================================================

    if visit_note.appointment_id is not None:

        appointment = get_appointment(
            db,
            visit_note.appointment_id
        )

        if appointment is None:
            raise ValueError(
                "Appointment not found."
            )

    # ========================================================
    # CREATE VISIT NOTE
    # ========================================================

    current_time = get_current_bangladesh_time()

    db_visit_note = models.VisitNote(
        patient_name=visit_note.patient_name,
        doctor_name=visit_note.doctor_name,
        appointment_id=visit_note.appointment_id,
        visit_date=visit_note.visit_date,
        notes=visit_note.notes,
        prescription=visit_note.prescription,
        status="active",
        created_at=current_time,
        updated_at=current_time
    )

    db.add(db_visit_note)
    db.commit()
    db.refresh(db_visit_note)

    return db_visit_note


def get_visit_notes(
    db: Session,
    patient_name: str | None = None
):
    query = (
        db.query(models.VisitNote)
        .filter(
            models.VisitNote.status != "archived"
        )
    )

    if patient_name:
        query = query.filter(
            models.VisitNote.patient_name
            == patient_name
        )

    return (
        query
        .order_by(
            models.VisitNote.visit_date.desc()
        )
        .all()
    )


def get_visit_note(
    db: Session,
    visit_note_id: int
):
    return (
        db.query(models.VisitNote)
        .filter(
            models.VisitNote.id == visit_note_id
        )
        .first()
    )


def update_visit_note(
    db: Session,
    visit_note_id: int,
    visit_note: schemas.VisitNoteUpdate
):
    db_visit_note = get_visit_note(
        db,
        visit_note_id
    )

    if db_visit_note is None:
        return None

    if visit_note.notes is not None:
        db_visit_note.notes = (
            visit_note.notes
        )

    if visit_note.prescription is not None:
        db_visit_note.prescription = (
            visit_note.prescription
        )

    db_visit_note.updated_at = (
        get_current_bangladesh_time()
    )

    db.commit()
    db.refresh(db_visit_note)

    return db_visit_note


def archive_visit_note(
    db: Session,
    visit_note_id: int
):
    db_visit_note = get_visit_note(
        db,
        visit_note_id
    )

    if db_visit_note is None:
        return None

    db_visit_note.status = "archived"

    db_visit_note.updated_at = (
        get_current_bangladesh_time()
    )

    db.commit()
    db.refresh(db_visit_note)

    return db_visit_note