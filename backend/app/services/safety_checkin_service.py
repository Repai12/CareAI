from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models import User, EmergencyContact, SafetyCheckin
from app.config import settings
from app.services.twilio_service import send_sms


safety_scheduler = BackgroundScheduler()


def check_missed_safety_checkins():
    db = SessionLocal()

    try:
        patients = (
            db.query(User)
            .filter(User.role == "patient")
            .all()
        )

        timeout = timedelta(
            hours=settings.SAFETY_CHECKIN_TIMEOUT_HOURS
        )

        now = datetime.utcnow()

        for patient in patients:
            latest_checkin = (
                db.query(SafetyCheckin)
                .filter(SafetyCheckin.user_id == patient.id)
                .order_by(SafetyCheckin.checked_in_at.desc())
                .first()
            )

            if latest_checkin is None:
                continue

            if not latest_checkin.is_checked_in:
                continue

            if now - latest_checkin.checked_in_at <= timeout:
                continue

            latest_checkin.is_checked_in = False
            db.commit()

            contacts = (
                db.query(EmergencyContact)
                .filter(
                    EmergencyContact.user_id == patient.id
                )
                .order_by(EmergencyContact.priority.asc())
                .all()
            )

            message = (
                f"CAREAI SAFETY ALERT! "
                f"{patient.name} has missed the daily safety check-in. "
                f"No check-in was received for more than "
                f"{settings.SAFETY_CHECKIN_TIMEOUT_HOURS} hours. "
                f"Please check on the patient."
            )

            for contact in contacts:
                try:
                    send_sms(contact.phone, message)
                except Exception as e:
                    print(
                        f"[safety-checkin] SMS failed for "
                        f"{contact.phone}: {e}"
                    )

    except Exception as e:
        print(f"[safety-checkin] Scheduler error: {e}")

    finally:
        db.close()


def start_safety_checkin_scheduler():
    if safety_scheduler.running:
        return

    safety_scheduler.add_job(
        check_missed_safety_checkins,
        "interval",
        hours=1,
        id="safety_checkin_job",
        replace_existing=True,
    )

    safety_scheduler.start()
