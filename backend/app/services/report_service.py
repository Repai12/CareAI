"""
services/report_service.py
-----------------------------
OWNED BY MEMBER 4 (Repai) - Module 2, Feature 4 core logic. Pulls 7 days
of real data, builds the HTML email, sends via Resend, logs every attempt.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment
from app.models.email_log import EmailLog
from app.services.email_service import send_email
from app.services.notification_service import create_notification
from app.models.notification import NotificationCategory


def _build_summary_html(patient: User, vitals: list[VitalsLog], meds: list[Medication], appts: list[Appointment]) -> str:
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

    return f"""
    <h2>Weekly Health Report for {patient.name}</h2>
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
    # Medications have no patient linkage in the current schema (Afifa's
    # migration dropped patient_id/active) - omit rather than send another
    # patient's medications in this patient's weekly report.
    meds = []
    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_email == patient.email, Appointment.appointment_date >= datetime.utcnow().date())
        .all()
    )

    html = _build_summary_html(patient, vitals, meds, appts)

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
