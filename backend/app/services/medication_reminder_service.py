"""
services/medication_reminder_service.py
-------------------------------------------
Closes a real gap in the Medicine Reminder & Adherence Tracker (README
S8.4): scheduling a reminder (medication_logs.py's create_medication_log)
only ever created a "pending" row - nothing ever reminded the patient
when it came due, and nothing ever transitioned an ignored reminder to
"missed". That meant the adherence tracker's whole "3 consecutive misses
triggers a notification" feature could never actually fire on its own -
it needed a human to manually click "Missed" on every single overdue
dose first, defeating the point of an *automated* tracker.

Runs on a timer (see scheduler.py, every 15 minutes - reminders are
time-of-day specific, unlike the once-daily jobs elsewhere in this app):
- A dose whose scheduled time has arrived and hasn't been reminded about
  yet gets one in-app notification ("time to take X"), not a text
  message - this app doesn't collect the patient's own phone number
  (only emergency contacts have one), so SMS-to-self isn't available
  without a bigger registration change.
- A dose still "pending" GRACE_PERIOD_MINUTES after its scheduled time
  is auto-marked missed and run through the existing missed-streak
  check, so the 3-in-a-row alert actually works without someone
  manually bookkeeping every dose.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.medication import Medication, MedicationLog, MedicationLogStatus
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.medication_logs import check_missed_streak

GRACE_PERIOD_MINUTES = 120


def run_medication_reminders(db: Session) -> None:
    now = datetime.utcnow()

    # 1. Due-now reminders that haven't been sent yet.
    due_now = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.status == MedicationLogStatus.pending.value,
            MedicationLog.scheduled_at <= now,
            MedicationLog.reminder_sent_at.is_(None),
        )
        .all()
    )
    for log in due_now:
        medication = db.query(Medication).filter(Medication.id == log.medication_id).first()
        if not medication:
            continue
        create_notification(
            db,
            patient_id=log.patient_id,
            event_type="MEDICATION_REMINDER",
            title="Medication reminder",
            message=f"Time to take {medication.medicine_name} ({medication.dosage}).",
            category=NotificationCategory.medication,
        )
        log.reminder_sent_at = now
    if due_now:
        db.commit()

    # 2. Overdue-by-more-than-the-grace-period reminders get auto-marked
    # missed, same status transition mark_missed() does by hand.
    overdue_cutoff = now - timedelta(minutes=GRACE_PERIOD_MINUTES)
    overdue = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.status == MedicationLogStatus.pending.value,
            MedicationLog.scheduled_at <= overdue_cutoff,
        )
        .all()
    )
    for log in overdue:
        log.status = MedicationLogStatus.missed.value
        db.commit()
        medication = db.query(Medication).filter(Medication.id == log.medication_id).first()
        if medication:
            check_missed_streak(db, medication, log)
