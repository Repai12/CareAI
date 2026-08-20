"""
routers/companion.py
-----------------------
Module 3: Dual-Persona AI Companion (README Features table). Patient-
only - this is the patient's own companion, not a family/doctor-facing
tool. Each persona (companion/coach) keeps its own separate message
thread so switching personas doesn't mix contexts.

Endpoints:
    GET  /companion/{patient_id}?persona=   - message history for that persona (patient, self only)
    POST /companion/{patient_id}            - send a message, get a reply (patient, self only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole
from app.models.companion import CompanionMessage, CompanionPersona, CompanionRole
from app.schemas import CompanionMessageCreate, CompanionMessageOut
from app.services.groq_health_service import companion_reply

router = APIRouter(prefix="/companion", tags=["companion"])

VALID_PERSONAS = {p.value for p in CompanionPersona}
HISTORY_TURNS = 10
MAX_MESSAGE_LENGTH = 2000


def _assert_self(patient_id: UUID, current_user: User):
    if current_user.role != UserRole.patient.value or current_user.id != patient_id:
        raise HTTPException(403, "The AI companion is only available to the patient themselves")


@router.get("/{patient_id}", response_model=list[CompanionMessageOut])
def get_companion_history(
    patient_id: UUID,
    persona: str = "companion",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_self(patient_id, current_user)
    if persona not in VALID_PERSONAS:
        raise HTTPException(422, f"persona must be one of {sorted(VALID_PERSONAS)}")

    return (
        db.query(CompanionMessage)
        .filter(CompanionMessage.patient_id == patient_id, CompanionMessage.persona == persona)
        .order_by(CompanionMessage.created_at)
        .all()
    )


@router.post("/{patient_id}", response_model=CompanionMessageOut)
def send_companion_message(
    patient_id: UUID,
    payload: CompanionMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_self(patient_id, current_user)
    if payload.persona not in VALID_PERSONAS:
        raise HTTPException(422, f"persona must be one of {sorted(VALID_PERSONAS)}")
    if not payload.message.strip():
        raise HTTPException(422, "Message cannot be empty.")
    if len(payload.message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(422, f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer.")

    prior = (
        db.query(CompanionMessage)
        .filter(CompanionMessage.patient_id == patient_id, CompanionMessage.persona == payload.persona)
        .order_by(CompanionMessage.created_at.desc())
        .limit(HISTORY_TURNS)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(prior)]

    reply = companion_reply(db, patient_id, payload.persona, history, payload.message.strip())
    if reply is None:
        raise HTTPException(503, "The AI companion is temporarily unavailable. Please try again shortly.")

    user_msg = CompanionMessage(
        patient_id=patient_id, persona=payload.persona, role=CompanionRole.user.value, content=payload.message.strip()
    )
    assistant_msg = CompanionMessage(
        patient_id=patient_id, persona=payload.persona, role=CompanionRole.assistant.value, content=reply
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg
