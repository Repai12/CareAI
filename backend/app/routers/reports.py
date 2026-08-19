"""
routers/reports.py
--------------------
OWNED BY MEMBER 4 (Repai) - Module 2, Feature 4: Automated Weekly Email
Health Report.
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.email_log import EmailLog
from app.schemas import EmailLogOut, TriggerReportRequest
from app.services.report_service import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["weekly reports"])

# Guards against an accidental double-click (or a deliberately malicious
# repeat call) spamming every linked family member/doctor with duplicate
# copies of the same report - README S7.4's "not re-send duplicates"
# requirement applied to the manual trigger, not just the scheduled job.
RESEND_COOLDOWN_HOURS = 24


def _assert_can_trigger(patient_id: uuid.UUID, current_user: User, db: Session):
    """
    Previously this endpoint only checked the caller's *role*, not
    whether they had any relationship to patient_id at all - a patient
    could pass any other patient's id and trigger emails about that
    stranger's health data to that stranger's family/doctor, and a
    doctor could do the same for a patient they were never linked to.
    Every other patient-scoped endpoint in this app re-checks ownership;
    this one had been missed.
    """
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only trigger their own report")
        return
    if current_user.role == UserRole.doctor.value:
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
            raise HTTPException(403, "You are not linked to this patient")
        return
    raise HTTPException(403, "Not allowed to trigger reports")


def _assert_can_view_history(patient_id: uuid.UUID, current_user: User, db: Session):
    """
    Looser than _assert_can_trigger: a family member can't manually
    re-send the report, but they're one of its recipients and should
    still be able to see whether/when it went out - and, same as every
    other patient-scoped endpoint, this must not be reachable by an
    unrelated account (the original version of this endpoint had no
    auth check at all, leaking recipient emails to any valid token).
    """
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own report history")
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
        raise HTTPException(403, "You do not have access to this patient's report history")


@router.post("/weekly/trigger", response_model=list[EmailLogOut])
def trigger_weekly_report(
    payload: TriggerReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_trigger(payload.patient_id, current_user, db)

    cooldown_start = datetime.utcnow() - timedelta(hours=RESEND_COOLDOWN_HOURS)
    recent = (
        db.query(EmailLog)
        .filter(
            EmailLog.patient_id == payload.patient_id,
            EmailLog.report_type == "WEEKLY_REPORT",
            EmailLog.status == "SENT",
            EmailLog.sent_at >= cooldown_start,
        )
        .first()
    )
    if recent:
        raise HTTPException(
            429,
            f"A report was already sent within the last {RESEND_COOLDOWN_HOURS} hours. "
            "Please wait before sending another.",
        )

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
    _assert_can_view_history(patient_id, current_user, db)
    return (
        db.query(EmailLog)
        .filter(EmailLog.patient_id == patient_id, EmailLog.report_type == "WEEKLY_REPORT")
        .order_by(EmailLog.sent_at.desc())
        .all()
    )
