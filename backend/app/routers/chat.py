"""
routers/chat.py
------------------
Module 3: Family Chat (README Features table, Tech Stack: "Real-time:
WebSockets (family/doctor chat)"). One room per patient - the patient
themselves plus anyone actively linked to them (family/doctor) share a
single thread, same access bar as the dashboard.

Endpoints:
    GET /chat/{patient_id}/messages   - message history (REST, loaded before the socket connects)
    WS  /ws/chat/{patient_id}         - live connection; token passed as a query param since the
                                         browser WebSocket API can't set an Authorization header
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.auth import get_current_user, decode_access_token
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.chat import ChatMessage
from app.schemas import ChatMessageOut
from app.services.chat_manager import manager

router = APIRouter(tags=["chat"])

MAX_MESSAGE_LENGTH = 2000


def _can_access_room(patient_id: UUID, user: User, db: Session) -> bool:
    if user.role == UserRole.patient.value:
        return user.id == patient_id
    return (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == user.id,
            CareLink.status == CareLinkStatus.active.value,
        )
        .first()
        is not None
    )


@router.get("/chat/{patient_id}/messages", response_model=list[ChatMessageOut])
def get_chat_history(
    patient_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _can_access_room(patient_id, current_user, db):
        raise HTTPException(403, "You do not have access to this patient's chat")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.patient_id == patient_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return list(reversed(messages))


@router.websocket("/ws/chat/{patient_id}")
async def chat_websocket(websocket: WebSocket, patient_id: UUID, token: str = ""):
    db = SessionLocal()
    try:
        user_id = decode_access_token(token)
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        if user is None or not _can_access_room(patient_id, user, db):
            await websocket.close(code=4403)
            return
    finally:
        db.close()

    await manager.connect(patient_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            content = text.strip()
            if not content:
                continue
            content = content[:MAX_MESSAGE_LENGTH]

            db = SessionLocal()
            try:
                msg = ChatMessage(
                    patient_id=patient_id,
                    sender_id=user.id,
                    sender_name=user.name,
                    sender_role=user.role,
                    content=content,
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)
                payload = ChatMessageOut.model_validate(msg).model_dump(mode="json")
            finally:
                db.close()

            await manager.broadcast(patient_id, payload)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(patient_id, websocket)
