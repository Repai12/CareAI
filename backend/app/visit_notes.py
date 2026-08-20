"""
visit_notes.py
------------------
OWNED BY MEMBER 2 (Afifa) - Doctor Visit History & Prescriptions
(README S8.3). Rewritten from the original version, which had no
authentication at all and referenced a VisitNote model class that was
never actually defined - see models/medication.py for the real one,
added alongside this rewrite.

Only doctors can write notes, and only for a patient they're actively
linked to. Editing/archiving is further restricted to the doctor who
wrote the note - "doctors can edit/archive their own notes but not
another doctor's if a patient has more than one" (S8.3's explicit rule).
Patients and any linked family/doctor can read the full history.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from .models.medication import Appointment, VisitNote
from .models.notification import NotificationCategory
from .services.notification_service import create_notification
from .services.groq_health_service import summarize_prescription
from .schemas import VisitNoteCreate, VisitNoteUpdate, VisitNoteResponse

router = APIRouter(prefix="/visit-notes", tags=["Doctor Visit History"])

BANGLADESH_TZ = ZoneInfo("Asia/Dhaka")


def get_current_bangladesh_date() -> date:
    return datetime.now(BANGLADESH_TZ).date()


def _assert_can_view(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own visit notes")
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
        raise HTTPException(403, "You do not have access to this patient's visit notes")


def _assert_is_treating_doctor(patient_id: UUID, current_user: User, db: Session):
    if current_user.role != UserRole.doctor.value:
        raise HTTPException(403, "Only doctors can write visit notes")
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
        raise HTTPException(403, "You are not an active, managing doctor for this patient")


def _get_patient_or_404(patient_id: UUID, db: Session) -> User:
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.post("/{patient_id}", response_model=VisitNoteResponse)
def create_visit_note(
    patient_id: UUID,
    payload: VisitNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_is_treating_doctor(patient_id, current_user, db)

    if payload.appointment_id is not None:
        appt = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
        if appt is None:
            raise HTTPException(404, "Appointment not found.")

    if payload.visit_date > get_current_bangladesh_date():
        raise HTTPException(400, "Visit date cannot be in the future.")

    now = datetime.utcnow()
    note = VisitNote(
        patient_id=patient_id,
        patient_name=patient.name,
        doctor_id=current_user.id,
        doctor_name=current_user.name,
        appointment_id=payload.appointment_id,
        visit_date=payload.visit_date,
        notes=payload.notes,
        prescription=payload.prescription,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    create_notification(
        db,
        patient_id=patient_id,
        event_type="DOCTOR_NOTE_ADDED",
        title="New doctor note",
        message=f"{current_user.name} added a visit note for {patient.name}.",
        category=NotificationCategory.appointment,
    )
    return note


@router.get("/{patient_id}", response_model=list[VisitNoteResponse])
def list_visit_notes(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_patient_or_404(patient_id, db)
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(VisitNote)
        .filter(VisitNote.patient_id == patient_id, VisitNote.status == "active")
        .order_by(VisitNote.visit_date.desc(), VisitNote.created_at.desc())
        .all()
    )


@router.get("/{patient_id}/{visit_note_id}", response_model=VisitNoteResponse)
def get_visit_note(
    patient_id: UUID,
    visit_note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    note = (
        db.query(VisitNote)
        .filter(VisitNote.id == visit_note_id, VisitNote.patient_id == patient_id, VisitNote.status == "active")
        .first()
    )
    if note is None:
        raise HTTPException(404, "Visit note not found.")
    return note


def _get_own_note_or_404(patient_id: UUID, visit_note_id: UUID, current_user: User, db: Session) -> VisitNote:
    if current_user.role != UserRole.doctor.value:
        raise HTTPException(403, "Only the doctor who wrote a note can edit or archive it")
    note = (
        db.query(VisitNote)
        .filter(VisitNote.id == visit_note_id, VisitNote.patient_id == patient_id, VisitNote.status == "active")
        .first()
    )
    if note is None:
        raise HTTPException(404, "Visit note not found.")
    if note.doctor_id != current_user.id:
        raise HTTPException(403, "You can only edit or archive your own visit notes")
    return note


@router.put("/{patient_id}/{visit_note_id}", response_model=VisitNoteResponse)
def update_visit_note(
    patient_id: UUID,
    visit_note_id: UUID,
    payload: VisitNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_own_note_or_404(patient_id, visit_note_id, current_user, db)

    if payload.notes is not None:
        if not payload.notes.strip():
            raise HTTPException(400, "Visit notes cannot be empty.")
        note.notes = payload.notes
        note.ai_summary = None  # stale now - regenerate on next request
    if payload.prescription is not None:
        note.prescription = payload.prescription
        note.ai_summary = None

    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


@router.post("/{patient_id}/{visit_note_id}/summarize", response_model=VisitNoteResponse)
def summarize_visit_note(
    patient_id: UUID,
    visit_note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI Prescription Summarizer (README Features table). Open to the
    patient and any actively-linked family/doctor - this is for the
    layperson audience, not doctor-only. Cached on the note so it's not
    regenerated (and doesn't burn a new Groq call) on every page view."""
    _assert_can_view(patient_id, current_user, db)
    note = (
        db.query(VisitNote)
        .filter(VisitNote.id == visit_note_id, VisitNote.patient_id == patient_id, VisitNote.status == "active")
        .first()
    )
    if note is None:
        raise HTTPException(404, "Visit note not found.")

    if note.ai_summary:
        return note

    summary = summarize_prescription(note.notes, note.prescription)
    if summary is None:
        raise HTTPException(503, "AI explanation is temporarily unavailable. Please try again shortly.")

    note.ai_summary = summary
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{patient_id}/{visit_note_id}")
def archive_visit_note(
    patient_id: UUID,
    visit_note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = _get_own_note_or_404(patient_id, visit_note_id, current_user, db)
    note.status = "archived"
    note.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Visit note archived successfully."}
