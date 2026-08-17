"""
routers/vitals.py
-------------------
OWNED BY MEMBER 1 (Mubasshira) - Vitals Logging, AI Health Report Analyzer,
AI Symptom Checker, AI Diet Advisor.

Endpoints:
    POST   /vitals                                  - log a vitals reading (patient only)
    GET    /vitals/{patient_id}/history              - view history (patient self, or linked family/doctor)
    PUT    /vitals/{vitals_id}                       - edit own reading
    DELETE /vitals/{vitals_id}                       - delete own reading

    POST   /vitals/reports/upload                    - upload a PDF, get a Groq summary (Feature 2)
    GET    /vitals/{patient_id}/reports               - list report history

    POST   /vitals/symptom-check                      - context-aware symptom check + urgency triage (Feature 3)
    GET    /vitals/{patient_id}/symptom-logs           - symptom check history

    POST   /vitals/diet-plan/generate                 - vitals-trend-aware diet plan (Feature 4)
    GET    /vitals/{patient_id}/diet-plan/latest        - latest plan + adherence history
    POST   /vitals/diet-plan/log                       - log adherence against a plan
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, PatientLink
from app.models.vitals import VitalsLog, HealthReport, SymptomLog, DietPlan, DietLog, UrgencyLevel
from app.schemas import (
    VitalsIn, VitalsUpdate, VitalsEntryOut, HealthReportOut,
    SymptomCheckIn, SymptomLogOut, DietPlanOut, DietLogIn, DietLogOut,
)
from app.services import groq_health_service as ai_service
from app.services.notification_service import create_notification
from app.models.notification import NotificationCategory

router = APIRouter(prefix="/vitals", tags=["vitals"])


# --- shared helpers (kept local to this file to avoid touching dashboard.py) ---

def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own records")
        return
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's records")


def _require_patient(current_user: User):
    if current_user.role != UserRole.patient.value:
        raise HTTPException(403, "Only the patient can record this")


def _is_abnormal(v: VitalsLog) -> bool:
    try:
        systolic, diastolic = (int(x) for x in v.blood_pressure.split("/"))
    except (ValueError, AttributeError):
        systolic = diastolic = None
    return bool(
        v.sugar_level > 140 or v.sugar_level < 70
        or v.heart_rate > 100 or v.heart_rate < 50
        or v.temperature > 37.8 or v.temperature < 35.5
        or (systolic is not None and (systolic > 140 or diastolic > 90))
    )


def _to_vitals_out(v: VitalsLog) -> VitalsEntryOut:
    return VitalsEntryOut(
        id=v.id, blood_pressure=v.blood_pressure, sugar_level=v.sugar_level,
        heart_rate=v.heart_rate, temperature=v.temperature, notes=v.notes,
        logged_at=v.logged_at, is_abnormal=_is_abnormal(v),
    )


# ---------------------------------------------------------------------------
# Feature 1: Vitals Logging System (CRUD)
# ---------------------------------------------------------------------------

VALID_RANGES = {
    "sugar_level": (20, 600, "Sugar level must be between 20 and 600 mg/dL"),
    "heart_rate": (20, 250, "Heart rate must be between 20 and 250 bpm"),
    "temperature": (30, 45, "Temperature must be between 30 and 45 °C"),
}


def _validate_ranges(payload):
    for field, (lo, hi, message) in VALID_RANGES.items():
        value = getattr(payload, field, None)
        if value is not None and not (lo <= value <= hi):
            raise HTTPException(422, message)


@router.post("", response_model=VitalsEntryOut)
def log_vitals(
    payload: VitalsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    _validate_ranges(payload)

    entry = VitalsLog(
        patient_id=current_user.id,
        blood_pressure=payload.blood_pressure,
        sugar_level=payload.sugar_level,
        heart_rate=payload.heart_rate,
        temperature=payload.temperature,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    if _is_abnormal(entry):
        create_notification(
            db, current_user.id,
            event_type="VITALS_ABNORMAL",
            title="Abnormal vitals reading logged",
            message=f"BP {entry.blood_pressure}, sugar {entry.sugar_level}, HR {entry.heart_rate}, temp {entry.temperature}°C",
            category=NotificationCategory.safety,
        )

    return _to_vitals_out(entry)


@router.get("/{patient_id}/history", response_model=list[VitalsEntryOut])
def get_vitals_history(
    patient_id: uuid.UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    entries = (
        db.query(VitalsLog)
        .filter(VitalsLog.patient_id == patient_id)
        .order_by(VitalsLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_vitals_out(v) for v in entries]


@router.put("/{vitals_id}", response_model=VitalsEntryOut)
def update_vitals(
    vitals_id: uuid.UUID,
    payload: VitalsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(VitalsLog).filter(VitalsLog.id == vitals_id).first()
    if not entry:
        raise HTTPException(404, "Vitals entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only edit your own vitals")

    _validate_ranges(payload)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return _to_vitals_out(entry)


@router.delete("/{vitals_id}")
def delete_vitals(
    vitals_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(VitalsLog).filter(VitalsLog.id == vitals_id).first()
    if not entry:
        raise HTTPException(404, "Vitals entry not found")
    if entry.patient_id != current_user.id:
        raise HTTPException(403, "You can only delete your own vitals")

    db.delete(entry)
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Feature 2: AI Health Report Analyzer
# ---------------------------------------------------------------------------

MAX_REPORT_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/reports/upload", response_model=HealthReportOut)
async def upload_health_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)

    if file.content_type != "application/pdf":
        raise HTTPException(422, "Only PDF files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_REPORT_BYTES:
        raise HTTPException(422, "File too large (max 10 MB)")

    extracted_text = ai_service.extract_pdf_text(file_bytes)
    summary = ai_service.summarize_health_report(extracted_text)

    report = HealthReport(
        patient_id=current_user.id,
        filename=file.filename or "report.pdf",
        file_data=file_bytes,
        extracted_text=extracted_text,
        ai_summary=summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    create_notification(
        db, current_user.id,
        event_type="HEALTH_REPORT_ANALYZED",
        title="New health report analyzed",
        message=f"AI summary ready for {report.filename}.",
        category=NotificationCategory.appointment,
    )

    return report


@router.get("/{patient_id}/reports", response_model=list[HealthReportOut])
def list_health_reports(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(HealthReport)
        .filter(HealthReport.patient_id == patient_id)
        .order_by(HealthReport.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Feature 3: AI Symptom Checker (context-aware + emergency auto-escalation)
# ---------------------------------------------------------------------------

@router.post("/symptom-check", response_model=SymptomLogOut)
def symptom_check(
    payload: SymptomCheckIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    if not payload.symptoms.strip():
        raise HTTPException(422, "Please describe your symptoms")

    result = ai_service.check_symptoms(db, current_user.id, payload.symptoms)
    is_emergency = result["urgency"] == UrgencyLevel.emergency.value

    log = SymptomLog(
        patient_id=current_user.id,
        symptoms=payload.symptoms,
        ai_response=result["advice"],
        urgency=result["urgency"],
        escalated=is_emergency,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Unique twist: an emergency-level result doesn't just sit in a log -
    # it immediately posts to the family Notification Center (Member 4's
    # shared feed) so someone actually sees it.
    if is_emergency:
        create_notification(
            db, current_user.id,
            event_type="SYMPTOM_CHECK_EMERGENCY",
            title="AI symptom checker flagged an emergency",
            message=f"Reported symptoms: {payload.symptoms[:200]}",
            category=NotificationCategory.emergency,
        )

    return log


@router.get("/{patient_id}/symptom-logs", response_model=list[SymptomLogOut])
def get_symptom_logs(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(SymptomLog)
        .filter(SymptomLog.patient_id == patient_id)
        .order_by(SymptomLog.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Feature 4: AI Diet Advisor (vitals-trend-aware plan + adherence tracking)
# ---------------------------------------------------------------------------

@router.post("/diet-plan/generate", response_model=DietPlanOut)
def generate_diet_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    result = ai_service.generate_diet_plan(db, current_user.id)

    plan = DietPlan(
        patient_id=current_user.id,
        based_on_summary=result["based_on_summary"],
        ai_plan=result["plan"],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{patient_id}/diet-plan/latest")
def get_latest_diet_plan(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    plan = (
        db.query(DietPlan)
        .filter(DietPlan.patient_id == patient_id)
        .order_by(DietPlan.created_at.desc())
        .first()
    )
    if not plan:
        return {"plan": None, "logs": [], "adherence_rate": None}

    logs = (
        db.query(DietLog)
        .filter(DietLog.plan_id == plan.id)
        .order_by(DietLog.logged_at.desc())
        .all()
    )
    followed_count = sum(1 for l in logs if l.followed)
    adherence_rate = round(followed_count / len(logs) * 100) if logs else None

    return {
        "plan": DietPlanOut.model_validate(plan),
        "logs": [DietLogOut.model_validate(l) for l in logs],
        "adherence_rate": adherence_rate,
    }


@router.post("/diet-plan/log", response_model=DietLogOut)
def log_diet_adherence(
    payload: DietLogIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    plan = db.query(DietPlan).filter(DietPlan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(404, "Diet plan not found")
    if plan.patient_id != current_user.id:
        raise HTTPException(403, "You can only log adherence against your own plan")

    log = DietLog(
        plan_id=payload.plan_id,
        patient_id=current_user.id,
        followed=payload.followed,
        note=payload.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
