"""
routers/notifications.py
----------------------------
OWNED BY MEMBER 4 (Repai) - Module 3, Feature 8: Family Notification
Center.

Corner cases handled per spec:
- Pagination: cursor-based (limit=20), not "return everything" - avoids
  UI freezes once a patient has a long event history.
- Concurrent mark-as-read: uses a single atomic UPDATE...WHERE statement
  instead of fetch-then-update, so two family members marking things
  read at the same moment can't race each other or double-count.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import update
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

PAGE_SIZE = 20


class NotificationOut(BaseModel):
    id: uuid.UUID
    event_type: str
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    next_cursor: Optional[str]  # pass this back as `before` to get the next page


class MarkReadRequest(BaseModel):
    notification_ids: Optional[list[uuid.UUID]] = None  # omit + mark_all=True to mark everything


def _assert_can_view_patient(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own notifications")
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
        raise HTTPException(403, "You do not have access to this patient's notifications")


@router.get("/{patient_id}", response_model=NotificationPage)
def get_notifications(
    patient_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Filter: EMERGENCY, MEDICATION, APPOINTMENT, SAFETY"),
    before: Optional[datetime] = Query(None, description="Cursor - return items older than this timestamp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view_patient(patient_id, current_user, db)

    query = db.query(Notification).filter(Notification.patient_id == patient_id)
    if category:
        query = query.filter(Notification.category == category)
    if before:
        query = query.filter(Notification.created_at < before)

    items = query.order_by(Notification.created_at.desc()).limit(PAGE_SIZE).all()
    next_cursor = items[-1].created_at.isoformat() if len(items) == PAGE_SIZE else None

    return NotificationPage(items=items, next_cursor=next_cursor)


@router.post("/{patient_id}/mark-read")
def mark_read(
    patient_id: uuid.UUID,
    payload: MarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view_patient(patient_id, current_user, db)

    # Single atomic UPDATE, not a fetch-then-save loop - this is what
    # prevents the "two family members mark-as-read at the same time"
    # race condition the spec calls out.
    stmt = update(Notification).where(Notification.patient_id == patient_id, Notification.is_read == False)  # noqa: E712
    if payload.notification_ids:
        stmt = stmt.where(Notification.id.in_(payload.notification_ids))
    stmt = stmt.values(is_read=True)

    result = db.execute(stmt)
    db.commit()
    return {"marked_read": result.rowcount}
