"""
services/daily_digest_service.py
-----------------------------------
"Automated daily digest" (README Features table, Module 3) - runs once
daily (see scheduler.py) for every patient, posting one lightweight
Notification Center entry summarizing the day: mood, vitals, medication
count, and check-in status. Deliberately an in-app notification, not
another daily email - the weekly report already owns the inbox slot,
and a daily email on top of that risks becoming exactly the kind of
noise that makes a family stop reading alerts altogether. Skips a
patient entirely if literally nothing happened today (no vitals, no
mood, no check-in) rather than posting a content-free "nothing to
report" every single day.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.vitals import VitalsLog
from app.models.mood import MoodLog
from app.models.medication import Medication
from app.models.safety_checkin import SafetyCheckin
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification


def _build_digest_message(patient: User, vitals_today, mood_today, active_med_count: int, checked_in: bool) -> str:
    parts = []
    if vitals_today:
        parts.append(f"vitals logged (BP {vitals_today.blood_pressure})")
    if mood_today:
        parts.append(f"mood: {mood_today.mood}")
    parts.append(f"{active_med_count} active medication(s)")
    parts.append("checked in today" if checked_in else "no check-in yet today")
    return f"{patient.name}'s day: " + "; ".join(parts) + "."


def run_daily_digest(db: Session) -> None:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = today_start.date()
    patients = db.query(User).filter(User.role == UserRole.patient.value).all()

    for patient in patients:
        vitals_today = (
            db.query(VitalsLog)
            .filter(VitalsLog.patient_id == patient.id, VitalsLog.logged_at >= today_start)
            .order_by(VitalsLog.logged_at.desc())
            .first()
        )
        mood_today = (
            db.query(MoodLog)
            .filter(MoodLog.patient_id == patient.id, MoodLog.logged_at >= today_start)
            .order_by(MoodLog.logged_at.desc())
            .first()
        )
        checked_in_today = (
            db.query(SafetyCheckin)
            .filter(SafetyCheckin.user_id == patient.id, SafetyCheckin.checked_in_at >= today_start)
            .first()
        )

        # Nothing at all happened today - skip rather than post a
        # content-free digest (real activity, not calendar days, is what
        # earns a notification).
        if not vitals_today and not mood_today and not checked_in_today:
            continue

        active_med_count = (
            db.query(Medication)
            .filter(
                Medication.patient_id == patient.id,
                (Medication.start_date.is_(None)) | (Medication.start_date <= today),
                (Medication.end_date.is_(None)) | (Medication.end_date >= today),
            )
            .count()
        )

        message = _build_digest_message(patient, vitals_today, mood_today, active_med_count, bool(checked_in_today))
        create_notification(
            db,
            patient_id=patient.id,
            event_type="DAILY_DIGEST",
            title="Daily digest",
            message=message,
            category=NotificationCategory.digest,
        )
