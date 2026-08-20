"""
services/report_service.py
-----------------------------
OWNED BY MEMBER 4 (Repai) - Module 2, Feature 4 core logic. Pulls 7 days
of real data, builds the HTML email, sends via Resend, logs every attempt.
"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment
from app.models.mood import MoodLog
from app.models.email_log import EmailLog
from app.services.email_service import send_email
from app.services.notification_service import create_notification
from app.models.notification import NotificationCategory
from app.services.groq_health_service import summarize_weekly_report


def _vitals_summary_text(vitals: list[VitalsLog]) -> str:
    if not vitals:
        return "No vitals logged this week."
    avg_sugar = sum(v.sugar_level for v in vitals) / len(vitals)
    avg_hr = sum(v.heart_rate for v in vitals) / len(vitals)
    return f"{len(vitals)} reading(s) logged, latest BP {vitals[-1].blood_pressure}, average sugar {avg_sugar:.0f} mg/dL, average heart rate {avg_hr:.0f} bpm."


def _mood_summary_text(moods: list[MoodLog]) -> str:
    if not moods:
        return "No mood entries logged this week."
    counts: dict[str, int] = {}
    for m in moods:
        counts[m.mood] = counts.get(m.mood, 0) + 1
    breakdown = ", ".join(f"{count}x {mood}" for mood, count in counts.items())
    return f"{len(moods)} entr{'y' if len(moods) == 1 else 'ies'} logged ({breakdown})."


def _build_summary_html(
    patient: User,
    vitals: list[VitalsLog],
    meds: list[Medication],
    appts: list[Appointment],
    ai_narrative: str | None,
) -> str:
    vitals_rows = "".join(
        f"<tr><td>{v.logged_at.strftime('%d %b, %H:%M')}</td>"
        f"<td>{v.blood_pressure}</td><td>{v.sugar_level}</td>"
        f"<td>{v.heart_rate}</td><td>{v.temperature}</td></tr>"
        for v in vitals
    ) or "<tr><td colspan='5'>No vitals logged this week</td></tr>"

    meds_rows = "".join(
        f"<li>{m.medicine_name} - {m.dosage} ({m.frequency})</li>" for m in meds
    ) or "<li>No active medications</li>"

    appt_rows = "".join(
        f"<li>{a.doctor_name} on {a.appointment_date.strftime('%d %b %Y')} at {a.start_time.strftime('%H:%M')}</li>" for a in appts
    ) or "<li>No upcoming appointments</li>"

    narrative_html = (
        f"""<div style="background:#F4F7F6;border-left:4px solid #C79A3B;padding:12px 16px;margin-bottom:16px;">
              <p style="margin:0 0 4px;font-size:12px;color:#888;">AI-generated summary, not a diagnosis - review before acting on it.</p>
              <p style="margin:0;">{ai_narrative}</p>
            </div>"""
        if ai_narrative
        else ""
    )

    return f"""
    <h2>Weekly Health Report for {patient.name}</h2>
    {narrative_html}
    <h3>Vitals (last 7 days)</h3>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Date</th><th>BP</th><th>Sugar</th><th>Heart Rate</th><th>Temp</th></tr>
      {vitals_rows}
    </table>
    <h3>Active Medications</h3>
    <ul>{meds_rows}</ul>
    <h3>Upcoming Appointments</h3>
    <ul>{appt_rows}</ul>
    <p>This is an automated report from CareAI.</p>
    """


def generate_weekly_report(db: Session, patient_id) -> list[EmailLog]:
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient.value).first()
    if not patient:
        raise ValueError("Patient not found")

    week_ago = datetime.utcnow() - timedelta(days=7)

    vitals = (
        db.query(VitalsLog)
        .filter(VitalsLog.patient_id == patient_id, VitalsLog.logged_at >= week_ago)
        .order_by(VitalsLog.logged_at)
        .all()
    )
    # Medication.patient_id was re-added in migration 56b76de96e84 - this
    # comment used to say it was permanently gone (stale; found live via
    # the same bug in ai_summary_service.py: the report always claimed
    # "no active medications" regardless of reality).
    today = date.today()
    meds = (
        db.query(Medication)
        .filter(
            Medication.patient_id == patient_id,
            (Medication.start_date.is_(None)) | (Medication.start_date <= today),
            (Medication.end_date.is_(None)) | (Medication.end_date >= today),
        )
        .all()
    )
    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_email == patient.email, Appointment.appointment_date >= datetime.utcnow().date())
        .all()
    )
    moods = (
        db.query(MoodLog)
        .filter(MoodLog.patient_id == patient_id, MoodLog.logged_at >= week_ago)
        .order_by(MoodLog.logged_at)
        .all()
    )

    # README names this feature "AI weekly health summaries" - the report
    # previously only ever sent raw tables, no actual AI narrative.
    # Grounded only in this week's real data; None (Groq unavailable)
    # degrades gracefully to just the tables, same as every other AI
    # feature in this app.
    ai_narrative = summarize_weekly_report(
        patient.name, _vitals_summary_text(vitals), _mood_summary_text(moods), len(appts), len(meds)
    )

    html = _build_summary_html(patient, vitals, meds, appts, ai_narrative)

    recipients = (
        db.query(User)
        .join(CareLink, CareLink.viewer_id == User.id)
        .filter(CareLink.patient_id == patient_id, CareLink.status == CareLinkStatus.active.value)
        .all()
    )

    logs = []
    for recipient in recipients:
        # Unlinked/missing email guard - skip cleanly instead of crashing the loop
        if not recipient.email:
            continue

        # send_email() itself never raises (returns False on any failure,
        # including no API key configured), but this stays defensive
        # per-recipient anyway - the same "one bad recipient can't take
        # down the rest of the batch" rule used for SOS/fall-alert SMS
        # applies here: one family member's bounced/invalid address must
        # not stop the doctor's copy of the same report from sending.
        try:
            success = send_email(
                to_email=recipient.email,
                subject=f"CareAI Weekly Health Report - {patient.name}",
                html_content=html,
            )
        except Exception as e:
            print(f"[weekly report] unexpected error emailing {recipient.email}: {e}")
            success = False

        log = EmailLog(
            patient_id=patient_id,
            recipient_email=recipient.email,
            report_type="WEEKLY_REPORT",
            summary_text=html,
            status="SENT" if success else "FAILED",
        )
        db.add(log)
        logs.append(log)

    db.commit()
    for log in logs:
        db.refresh(log)

    # Add a family-visible event so the Notification Center reflects
    # this real action, not just the EmailLog audit table.
    if logs:
        any_failed = any(l.status == "FAILED" for l in logs)
        create_notification(
            db, patient_id,
            event_type="REPORT_SENT" if not any_failed else "REPORT_FAILED",
            title="Weekly health report sent" if not any_failed else "Weekly report had a delivery issue",
            message=f"Sent to {len(logs)} recipient(s) for {patient.name}.",
            category=NotificationCategory.appointment,
        )

    return logs
