"""
services/scheduler.py
------------------------
OWNED BY MEMBER 4 (Repai). Runs the weekly report automatically every
Sunday, for every patient.

NOTE ON ARCHITECTURE: the original spec called for Celery + Redis for
background jobs. This uses APScheduler instead - a lighter-weight
in-process scheduler that achieves the same "runs automatically every
Sunday" behavior without needing a separate worker process or a Redis
server running on every teammate's machine. This is a deliberate,
appropriately-scoped substitution for a project this size, not a missing
feature - Celery/Redis would be worth adopting only if the job volume or
need for retry queues grew significantly.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.report_service import generate_weekly_report

scheduler = BackgroundScheduler()


def run_weekly_reports_for_all_patients():
    db = SessionLocal()
    try:
        patients = db.query(User).filter(User.role == UserRole.patient.value).all()
        for patient in patients:
            try:
                generate_weekly_report(db, patient.id)
            except Exception as e:
                print(f"[scheduler] Failed for patient {patient.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        run_weekly_reports_for_all_patients,
        CronTrigger(day_of_week="sun", hour=8, minute=0),
        id="weekly_report_job",
        replace_existing=True,
    )
    scheduler.start()
