from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment, VisitNote
from .schemas import (
    VisitNoteCreate,
    VisitNoteUpdate,
    VisitNoteResponse,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/visit-notes",
    tags=["Doctor Visit History"]
)


# ============================================================
# BANGLADESH TIMEZONE
# ============================================================

BANGLADESH_TZ = ZoneInfo("Asia/Dhaka")


# ============================================================
# HELPER — CURRENT BANGLADESH DATE/TIME
# ============================================================

def get_current_bangladesh_datetime() -> datetime:
    return datetime.now(BANGLADESH_TZ)


def get_current_bangladesh_date() -> date:
    return get_current_bangladesh_datetime().date()


# ============================================================
# CREATE VISIT NOTE
# ============================================================

@router.post(
    "/",
    response_model=VisitNoteResponse
)
def create_visit_note(
    visit_note: VisitNoteCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Validate appointment if one was provided
    # --------------------------------------------------------

    if visit_note.appointment_id is not None:

        appointment = (
            db.query(Appointment)
            .filter(
                Appointment.id
                == visit_note.appointment_id
            )
            .first()
        )

        if appointment is None:

            raise HTTPException(
                status_code=404,
                detail="Appointment not found."
            )

    # --------------------------------------------------------
    # 2. Prevent future visit dates
    # --------------------------------------------------------

    current_date = get_current_bangladesh_date()

    if visit_note.visit_date > current_date:

        raise HTTPException(
            status_code=400,
            detail=(
                "Visit date cannot be in the future."
            )
        )

    # --------------------------------------------------------
    # 3. Create visit note
    # --------------------------------------------------------

    now = get_current_bangladesh_datetime()

    new_visit_note = VisitNote(
        patient_name=visit_note.patient_name,
        doctor_name=visit_note.doctor_name,
        appointment_id=visit_note.appointment_id,
        visit_date=visit_note.visit_date,
        notes=visit_note.notes,
        prescription=visit_note.prescription,
        status="active",
        created_at=now,
        updated_at=now
    )

    db.add(new_visit_note)
    db.commit()
    db.refresh(new_visit_note)

    return new_visit_note


# ============================================================
# GET ALL VISIT NOTES
# ============================================================

@router.get(
    "/",
    response_model=list[VisitNoteResponse]
)
def get_visit_notes(
    db: Session = Depends(get_db)
):

    visit_notes = (
        db.query(VisitNote)
        .filter(
            VisitNote.status == "active"
        )
        .order_by(
            VisitNote.visit_date.desc(),
            VisitNote.created_at.desc()
        )
        .all()
    )

    return visit_notes


# ============================================================
# GET SINGLE VISIT NOTE
# ============================================================

@router.get(
    "/{visit_note_id}",
    response_model=VisitNoteResponse
)
def get_visit_note(
    visit_note_id: int,
    db: Session = Depends(get_db)
):

    visit_note = (
        db.query(VisitNote)
        .filter(
            VisitNote.id == visit_note_id,
            VisitNote.status == "active"
        )
        .first()
    )

    if visit_note is None:

        raise HTTPException(
            status_code=404,
            detail="Visit note not found."
        )

    return visit_note


# ============================================================
# GET VISIT NOTES FOR A SPECIFIC APPOINTMENT
# ============================================================

@router.get(
    "/appointment/{appointment_id}",
    response_model=list[VisitNoteResponse]
)
def get_visit_notes_for_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Check appointment exists
    # --------------------------------------------------------

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
    # 2. Get visit notes
    # --------------------------------------------------------

    visit_notes = (
        db.query(VisitNote)
        .filter(
            VisitNote.appointment_id
            == appointment_id,
            VisitNote.status == "active"
        )
        .order_by(
            VisitNote.visit_date.desc()
        )
        .all()
    )

    return visit_notes


# ============================================================
# UPDATE VISIT NOTE
# ============================================================

@router.put(
    "/{visit_note_id}",
    response_model=VisitNoteResponse
)
def update_visit_note(
    visit_note_id: int,
    visit_note_data: VisitNoteUpdate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find visit note
    # --------------------------------------------------------

    visit_note = (
        db.query(VisitNote)
        .filter(
            VisitNote.id == visit_note_id,
            VisitNote.status == "active"
        )
        .first()
    )

    if visit_note is None:

        raise HTTPException(
            status_code=404,
            detail="Visit note not found."
        )

    # --------------------------------------------------------
    # 2. Update notes if provided
    # --------------------------------------------------------

    if visit_note_data.notes is not None:

        if not visit_note_data.notes.strip():

            raise HTTPException(
                status_code=400,
                detail="Visit notes cannot be empty."
            )

        visit_note.notes = (
            visit_note_data.notes
        )

    # --------------------------------------------------------
    # 3. Update prescription if provided
    # --------------------------------------------------------

    if visit_note_data.prescription is not None:

        visit_note.prescription = (
            visit_note_data.prescription
        )

    # --------------------------------------------------------
    # 4. Update timestamp
    # --------------------------------------------------------

    visit_note.updated_at = (
        get_current_bangladesh_datetime()
    )

    db.commit()
    db.refresh(visit_note)

    return visit_note


# ============================================================
# DELETE / ARCHIVE VISIT NOTE
# ============================================================

@router.delete(
    "/{visit_note_id}"
)
def delete_visit_note(
    visit_note_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find visit note
    # --------------------------------------------------------

    visit_note = (
        db.query(VisitNote)
        .filter(
            VisitNote.id == visit_note_id,
            VisitNote.status == "active"
        )
        .first()
    )

    if visit_note is None:

        raise HTTPException(
            status_code=404,
            detail="Visit note not found."
        )

    # --------------------------------------------------------
    # 2. Archive instead of permanently deleting
    # --------------------------------------------------------

    visit_note.status = "archived"

    visit_note.updated_at = (
        get_current_bangladesh_datetime()
    )

    db.commit()

    return {
        "message":
            "Visit note archived successfully."
    }