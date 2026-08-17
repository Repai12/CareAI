"""
report_service.py
------------------
MODULE 2 - FEATURE 4 (Member-4 / Repai Ul Islam)
"[SendGrid API] Automated Weekly Email Health Report — SendGrid emails a
formatted weekly health summary to the patient's family and doctor."

generate_weekly_report():
  - Pulls the last 7 days of vitals, active medications, and appointments
    for a patient straight from Postgres (real data, no hardcoding).
  - Builds an HTML summary.
  - Sends it via SendGrid to every family/doctor linked to that patient.
  - Logs each send attempt to WeeklyReportLog (audit trail = real CRUD).
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import User, UserRole, Vitals, Medication, Appointment, PatientLink, WeeklyReportLog
from app.services.email_service import send_email


def _build_summary_html(patient: User, vitals: list[Vitals], meds: list[Medication], appts: list[Appointment]) -> str:
    vitals_rows = "".join(
        f"<tr><td>{v.recorded_at.strftime('%d %b, %H:%M')}</td>"
        f"<td>{v.blood_pressure}</td><td>{v.sugar_level}</td>"
        f"<td>{v.heart_rate}</td><td>{v.temperature}</td></tr>"
        for v in vitals
    ) or "<tr><td colspan='5'>No vitals logged this week</td></tr>"

    meds_rows = "".join(
        f"<li>{m.name} - {m.dosage} ({m.frequency})</li>" for m in meds
    ) or "<li>No active medications</li>"

    appt_rows = "".join(
        f"<li>{a.doctor_name} on {a.scheduled_at.strftime('%d %b %Y, %H:%M')}</li>" for a in appts
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


def generate_weekly_report(db: Session, patient_id) -> list[WeeklyReportLog]:
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.patient).first()
    if not patient:
        raise ValueError("Patient not found")

    week_ago = datetime.utcnow() - timedelta(days=7)

    vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id, Vitals.recorded_at >= week_ago)
        .order_by(Vitals.recorded_at)
        .all()
    )
    meds = (
        db.query(Medication)
        .filter(Medication.patient_id == patient_id, Medication.active == True)  # noqa: E712
        .all()
    )
    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id, Appointment.scheduled_at >= datetime.utcnow())
        .all()
    )

    html = _build_summary_html(patient, vitals, meds, appts)

    recipients = (
        db.query(User)
        .join(PatientLink, PatientLink.viewer_id == User.id)
        .filter(PatientLink.patient_id == patient_id)
        .all()
    )

    logs = []
    for recipient in recipients:
        success = send_email(
            to_email=recipient.email,
            subject=f"CareAI Weekly Health Report - {patient.name}",
            html_content=html,
        )
        log = WeeklyReportLog(
            patient_id=patient_id,
            sent_to=recipient.email,
            summary_text=html,
            status="sent" if success else "failed",
        )
        db.add(log)
        logs.append(log)

    db.commit()
    for log in logs:
        db.refresh(log)
    return logs
