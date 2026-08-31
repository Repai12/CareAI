"""
services/ai_summary_service.py
---------------------------------
OWNED BY MEMBER 4 (Repai) - Module 3, Feature 7: Doctor AI Patient
Summary Email.

Workflow: aggregates the last 30 days of a patient's logs (vitals,
medications, appointments - symptoms/diet logs will fold in once
Member 1 builds those tables), sends it to Gemini with a clinical
summary prompt, and hands the result to email_service.py (Gmail SMTP)
to actually deliver it.

Corner cases handled (per spec):
- Gemini timeout (>15s): falls back to emailing the raw formatted logs
  with an apology note instead of crashing.
- Rate limiting: enforces 1 call per patient per 5 minutes using an
  in-memory dict (see note on Celery/Redis substitution in scheduler.py -
  same reasoning applies here: a lightweight substitute is appropriate
  for this project's scale instead of standing up Redis).
"""

import time
from datetime import date, datetime, timedelta

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment
from app.models.email_log import EmailLog
from app.services.email_service import send_email
from app.services.notification_service import create_notification
from app.models.notification import NotificationCategory

genai.configure(api_key=settings.GEMINI_API_KEY)

GEMINI_TIMEOUT_SECONDS = 15
RATE_LIMIT_SECONDS = 5 * 60  # 1 call per patient per 5 minutes

# In-memory rate limit tracker: {patient_id: last_call_timestamp}
_last_call_at: dict = {}


class RateLimitedError(Exception):
    pass


def _check_rate_limit(patient_id) -> None:
    last = _last_call_at.get(str(patient_id))
    if last and (time.time() - last) < RATE_LIMIT_SECONDS:
        wait = int(RATE_LIMIT_SECONDS - (time.time() - last))
        raise RateLimitedError(f"Please wait {wait} seconds before generating another summary for this patient.")
    _last_call_at[str(patient_id)] = time.time()


def _gather_recent_logs(db: Session, patient: User) -> dict:
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    vitals = (
        db.query(VitalsLog)
        .filter(VitalsLog.patient_id == patient.id, VitalsLog.logged_at >= thirty_days_ago)
        .order_by(VitalsLog.logged_at)
        .all()
    )
    # Medication.patient_id was re-added in migration 56b76de96e84 (this
    # comment used to say it was permanently gone - stale, found live: the
    # AI summary was confidently telling doctors "no active medications"
    # for patients who plainly have some, since this always returned []).
    today = date.today()
    meds = (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient.id,
            (Medication.start_date.is_(None)) | (Medication.start_date <= today),
            (Medication.end_date.is_(None)) | (Medication.end_date >= today),
        )
        .all()
    )
    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_email == patient.email, Appointment.appointment_date >= thirty_days_ago.date())
        .all()
    )
    return {"vitals": vitals, "medications": meds, "appointments": appts}


def _format_raw_logs_html(patient: User, logs: dict) -> str:
    """Fallback formatting used both as the Gemini prompt input and as the
    emergency fallback email body if Gemini times out."""
    vitals_rows = "".join(
        f"<tr><td>{v.logged_at.strftime('%d %b')}</td><td>{v.blood_pressure}</td>"
        f"<td>{v.sugar_level}</td><td>{v.heart_rate}</td><td>{v.temperature}</td></tr>"
        for v in logs["vitals"]
    ) or "<tr><td colspan='5'>No vitals logged in the last 30 days</td></tr>"

    meds_rows = "".join(f"<li>{m.medicine_name} - {m.dosage} ({m.frequency})</li>" for m in logs["medications"]) or "<li>None</li>"
    appt_rows = "".join(
        f"<li>{a.doctor_name} on {a.appointment_date.strftime('%d %b %Y')}</li>" for a in logs["appointments"]
    ) or "<li>None</li>"

    return f"""
    <h3>Vitals (last 30 days)</h3>
    <table border="1" cellpadding="6"><tr><th>Date</th><th>BP</th><th>Sugar</th><th>HR</th><th>Temp</th></tr>{vitals_rows}</table>
    <h3>Active Medications</h3><ul>{meds_rows}</ul>
    <h3>Appointments (last 30 days)</h3><ul>{appt_rows}</ul>
    """


def _build_gemini_prompt(patient: User, logs: dict) -> str:
    raw_html = _format_raw_logs_html(patient, logs)
    return f"""
You are assisting a physician by summarizing a patient's recent health data.
Patient: {patient.name}

Raw data (HTML table, for your reference):
{raw_html}

Write a concise, plain-English clinical summary (4-6 sentences) covering:
overall vitals trend, medication adherence context, and anything a doctor
should notice before the next visit. Do not invent data not present above.
"""


def generate_doctor_ai_summary(db: Session, patient_id, requesting_doctor: User) -> EmailLog:
    _check_rate_limit(patient_id)

    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise ValueError("Patient not found")

    logs = _gather_recent_logs(db, patient)
    raw_html = _format_raw_logs_html(patient, logs)

    summary_html: str
    try:
        model = genai.GenerativeModel("gemini-3.5-flash")
        prompt = _build_gemini_prompt(patient, logs)
        response = model.generate_content(
            prompt,
            request_options={"timeout": GEMINI_TIMEOUT_SECONDS},
        )
        ai_text = response.text
        summary_html = f"<h2>AI Clinical Summary - {patient.name}</h2><p>{ai_text}</p>{raw_html}"
    except Exception as e:
        # Corner case: Gemini timeout/down - fall back to raw logs + apology,
        # never crash the endpoint just because the AI step failed.
        print(f"[Gemini error] {e}")
        summary_html = (
            f"<h2>Patient Summary - {patient.name}</h2>"
            f"<p><i>Our AI summarizer is temporarily unavailable, so here is the "
            f"raw data instead. Apologies for the inconvenience.</i></p>{raw_html}"
        )

    success = send_email(
        to_email=requesting_doctor.email,
        subject=f"CareAI - AI Patient Summary for {patient.name}",
        html_content=summary_html,
    )

    log = EmailLog(
        patient_id=patient_id,
        recipient_email=requesting_doctor.email,
        report_type="DOCTOR_AI_SUMMARY",
        summary_text=summary_html,
        status="SENT" if success else "FAILED",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    create_notification(
        db, patient_id,
        event_type="AI_SUMMARY_SENT" if success else "AI_SUMMARY_FAILED",
        title="Doctor requested an AI summary" if success else "AI summary delivery failed",
        message=f"Sent to {requesting_doctor.name} ({requesting_doctor.email}).",
        category=NotificationCategory.appointment,
    )

    return log
