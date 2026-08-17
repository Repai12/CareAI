"""
routers/reports.py
--------------------
OWNED BY MEMBER 4 (Repai) - Module 2, Feature 4: Automated Weekly Email
Health Report.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas import EmailLogOut, TriggerReportRequest
from app.services.report_service import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["weekly reports"])


@router.post("/weekly/trigger", response_model=list[EmailLogOut])
def trigger_weekly_report(
    payload: TriggerReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.patient.value, UserRole.doctor.value):
        raise HTTPException(403, "Not allowed to trigger reports")

    try:
        logs = generate_weekly_report(db, payload.patient_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    if not logs:
        raise HTTPException(400, "No family/doctor linked to this patient to email")

    return logs


@router.get("/weekly/{patient_id}", response_model=list[EmailLogOut])
def get_report_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.email_log import EmailLog
    return (
        db.query(EmailLog)
        .filter(EmailLog.patient_id == patient_id, EmailLog.report_type == "WEEKLY_REPORT")
        .order_by(EmailLog.sent_at.desc())
        .all()
    )
