"""
reports.py
----------
Exposes the weekly report feature over HTTP:
  POST /reports/weekly/trigger   - manually generate + send now (for demo/testing)
  GET  /reports/weekly/{patient_id} - view past report logs (real CRUD read)

The actual automatic "every week" scheduling is handled by
app/services/scheduler.py (APScheduler), started from main.py.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserRole, WeeklyReportLog
from app.schemas import WeeklyReportOut, TriggerReportRequest
from app.services.report_service import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["weekly reports"])


@router.post("/weekly/trigger", response_model=list[WeeklyReportOut])
def trigger_weekly_report(
    payload: TriggerReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only the patient themselves or a doctor can manually trigger it
    if current_user.role not in (UserRole.patient, UserRole.doctor):
        raise HTTPException(403, "Not allowed to trigger reports")

    try:
        logs = generate_weekly_report(db, payload.patient_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

    if not logs:
        raise HTTPException(400, "No family/doctor linked to this patient to email")

    return logs


@router.get("/weekly/{patient_id}", response_model=list[WeeklyReportOut])
def get_report_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(WeeklyReportLog)
        .filter(WeeklyReportLog.patient_id == patient_id)
        .order_by(WeeklyReportLog.sent_at.desc())
        .all()
    )
