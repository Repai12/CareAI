"""
routers/patient_qa.py
------------------------
Module 3: AI Patient History Q&A (README Features table). Doctor-only -
matches README's role line verbatim: "Doctor ... uses AI to analyze
reports, answers patient-history questions". Grounds every answer in the
patient's actual latest vitals, active medications, recent visit notes,
and recent symptom checks rather than a generic response.

Endpoints:
    POST /patient-qa/{patient_id}   - ask a question (doctor, actively-linked)
    GET  /patient-qa/{patient_id}   - past Q&A history (same access bar)
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from app.models.vitals import VitalsLog, SymptomLog
from app.models.medication import Medication, VisitNote
from app.models.patient_qa import PatientQuestion
from app.schemas import PatientQuestionCreate, PatientQuestionOut
from app.services.groq_health_service import answer_patient_question

router = APIRouter(prefix="/patient-qa", tags=["patient qa"])


def _assert_treating_doctor(patient_id: UUID, current_user: User, db: Session):
    if current_user.role != UserRole.doctor.value:
        raise HTTPException(403, "Only doctors can use the patient history Q&A tool")
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


def _build_patient_context(patient_id: UUID, db: Session) -> str:
    parts = []

    latest_vitals = (
        db.query(VitalsLog).filter(VitalsLog.patient_id == patient_id).order_by(VitalsLog.logged_at.desc()).first()
    )
    if latest_vitals:
        parts.append(
            f"Latest vitals ({latest_vitals.logged_at.strftime('%d %b %Y')}): "
            f"BP {latest_vitals.blood_pressure}, sugar {latest_vitals.sugar_level} mg/dL, "
            f"HR {latest_vitals.heart_rate} bpm, temp {latest_vitals.temperature}°C."
        )
    else:
        parts.append("No vitals on file.")

    today = date.today()
    active_meds = (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient_id,
            (Medication.start_date.is_(None)) | (Medication.start_date <= today),
            (Medication.end_date.is_(None)) | (Medication.end_date >= today),
        )
        .all()
    )
    if active_meds:
        parts.append("Active medications: " + "; ".join(f"{m.medicine_name} {m.dosage}" for m in active_meds) + ".")
    else:
        parts.append("No active medications on file.")

    recent_notes = (
        db.query(VisitNote)
        .filter(VisitNote.patient_id == patient_id, VisitNote.status == "active")
        .order_by(VisitNote.visit_date.desc())
        .limit(5)
        .all()
    )
    if recent_notes:
        parts.append(
            "Recent visit notes:\n"
            + "\n".join(f"- {n.visit_date}: {n.notes}" + (f" (Rx: {n.prescription})" if n.prescription else "") for n in recent_notes)
        )
    else:
        parts.append("No visit notes on file.")

    recent_symptoms = (
        db.query(SymptomLog).filter(SymptomLog.patient_id == patient_id).order_by(SymptomLog.created_at.desc()).limit(5).all()
    )
    if recent_symptoms:
        parts.append(
            "Recent symptom checks:\n"
            + "\n".join(f"- {s.created_at.strftime('%d %b')}: \"{s.symptoms}\" (urgency: {s.urgency})" for s in recent_symptoms)
        )

    return "\n\n".join(parts)


@router.post("/{patient_id}", response_model=PatientQuestionOut)
def ask_patient_question(
    patient_id: UUID,
    payload: PatientQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_treating_doctor(patient_id, current_user, db)

    if not payload.question.strip():
        raise HTTPException(422, "Question cannot be empty.")

    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise HTTPException(404, "Patient not found.")

    context = _build_patient_context(patient_id, db)
    answer = answer_patient_question(context, payload.question)
    if answer is None:
        raise HTTPException(503, "AI answer is temporarily unavailable. Please try again shortly.")

    entry = PatientQuestion(
        patient_id=patient_id,
        doctor_id=current_user.id,
        question=payload.question.strip(),
        answer=answer,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{patient_id}", response_model=list[PatientQuestionOut])
def get_patient_question_history(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_treating_doctor(patient_id, current_user, db)
    return (
        db.query(PatientQuestion)
        .filter(PatientQuestion.patient_id == patient_id, PatientQuestion.doctor_id == current_user.id)
        .order_by(PatientQuestion.created_at.desc())
        .all()
    )
