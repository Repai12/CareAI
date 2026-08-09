"""
scheduler.py
------------
Makes the weekly report truly "automated" (not just a manual button).
Uses APScheduler to run every Sunday at 08:00 and generate+send the report
for every patient in the system. Started once from main.py on app startup.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models import User, UserRole
from app.services.report_service import generate_weekly_report

scheduler = BackgroundScheduler()


def run_weekly_reports_for_all_patients():
    db = SessionLocal()
    try:
        patients = db.query(User).filter(User.role == UserRole.patient).all()
        for patient in patients:
            try:
                generate_weekly_report(db, patient.id)
            except Exception as e:
                print(f"[scheduler] Failed for patient {patient.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    # Every Sunday at 08:00 server time
    scheduler.add_job(
        run_weekly_reports_for_all_patients,
        CronTrigger(day_of_week="sun", hour=8, minute=0),
        id="weekly_report_job",
        replace_existing=True,
    )
    scheduler.start()
