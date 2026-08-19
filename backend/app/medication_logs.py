"""
medication_logs.py
---------------------
OWNED BY MEMBER 2 (Afifa) - Medicine Reminder & Adherence Tracker
(README S8.4). Rewritten from the original version, which had no
authentication at all and referenced a MedicationLog model class that
was never actually defined - see models/medication.py for the real one,
added alongside this rewrite.

"A single missed dose (or a streak) generates a notification - a single
missed pill isn't alarming, three days of missed doses is" (S8.4): only
the 3rd+ consecutive missed dose for a medication triggers a
notification, not every individual miss.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from .models.medication import Medication, MedicationLog, MedicationLogStatus
from .models.notification import NotificationCategory
from .services.notification_service import create_notification
from .schemas import MedicationLogCreate, MedicationLogResponse, MedicationAdherenceResponse

router = APIRouter(prefix="/medication-logs", tags=["Medication Logs"])

BANGLADESH_TZ = ZoneInfo("Asia/Dhaka")
MISSED_STREAK_ALERT_THRESHOLD = 3


def get_current_bangladesh_datetime() -> datetime:
    return datetime.now(BANGLADESH_TZ)


def make_bangladesh_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(BANGLADESH_TZ)
    return dt.replace(tzinfo=BANGLADESH_TZ)


def _assert_can_view(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own medication logs")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's medication logs")


def _assert_can_manage(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only manage their own medication logs")
        return
    link = (
        db.query(CareLink)
        .filter(
            CareLink.patient_id == patient_id,
            CareLink.viewer_id == current_user.id,
            CareLink.status == CareLinkStatus.active.value,
            CareLink.permission_level == CareLinkPermission.view_and_manage.value,
        )
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have permission to manage this patient's medication logs")


def _get_owned_medication(patient_id: UUID, medication_id: UUID, db: Session) -> Medication:
    medication = db.query(Medication).filter(Medication.id == medication_id, Medication.patient_id == patient_id).first()
    if medication is None:
        raise HTTPException(404, "Medication not found for this patient")
    return medication


@router.post("/{patient_id}", response_model=MedicationLogResponse)
def create_medication_log(
    patient_id: UUID,
    payload: MedicationLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    _get_owned_medication(patient_id, payload.medication_id, db)

    scheduled_at = make_bangladesh_datetime(payload.scheduled_at)
    if scheduled_at <= get_current_bangladesh_datetime():
        raise HTTPException(400, "Medication reminder cannot be scheduled in the past.")

    existing = (
        db.query(MedicationLog)
        .filter(MedicationLog.medication_id == payload.medication_id, MedicationLog.scheduled_at == payload.scheduled_at)
        .first()
    )
    if existing is not None:
        raise HTTPException(409, "A medication reminder already exists for this date and time.")

    log = MedicationLog(
        medication_id=payload.medication_id,
        patient_id=patient_id,
        scheduled_at=payload.scheduled_at,
        status=MedicationLogStatus.pending.value,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{patient_id}", response_model=list[MedicationLogResponse])
def list_medication_logs(
    patient_id: UUID,
    medication_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    query = db.query(MedicationLog).filter(MedicationLog.patient_id == patient_id)
    if medication_id:
        query = query.filter(MedicationLog.medication_id == medication_id)
    return query.order_by(MedicationLog.scheduled_at.desc()).all()


def _check_missed_streak(db: Session, medication: Medication, log: MedicationLog):
    """Notifies only once a medication has MISSED_STREAK_ALERT_THRESHOLD consecutive misses."""
    recent = (
        db.query(MedicationLog)
        .filter(MedicationLog.medication_id == medication.id, MedicationLog.status != MedicationLogStatus.pending.value)
        .order_by(MedicationLog.scheduled_at.desc())
        .limit(MISSED_STREAK_ALERT_THRESHOLD)
        .all()
    )
    if len(recent) < MISSED_STREAK_ALERT_THRESHOLD:
        return
    if all(l.status == MedicationLogStatus.missed.value for l in recent):
        create_notification(
            db,
            patient_id=medication.patient_id,
            event_type="MEDICATION_MISSED_STREAK",
            title="Missed medication streak",
            message=f"{medication.medicine_name} has been missed {MISSED_STREAK_ALERT_THRESHOLD} times in a row.",
            category=NotificationCategory.medication,
        )


@router.put("/{patient_id}/{log_id}/taken", response_model=MedicationLogResponse)
def mark_taken(
    patient_id: UUID,
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    log = db.query(MedicationLog).filter(MedicationLog.id == log_id, MedicationLog.patient_id == patient_id).first()
    if log is None:
        raise HTTPException(404, "Medication reminder not found.")
    if log.status == MedicationLogStatus.taken.value:
        raise HTTPException(400, "This medication reminder has already been marked as taken.")

    log.taken_at = get_current_bangladesh_datetime()
    log.status = MedicationLogStatus.taken.value
    db.commit()
    db.refresh(log)
    return log


@router.put("/{patient_id}/{log_id}/missed", response_model=MedicationLogResponse)
def mark_missed(
    patient_id: UUID,
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    log = db.query(MedicationLog).filter(MedicationLog.id == log_id, MedicationLog.patient_id == patient_id).first()
    if log is None:
        raise HTTPException(404, "Medication reminder not found.")
    if log.status == MedicationLogStatus.taken.value:
        raise HTTPException(400, "A medication already marked as taken cannot be marked as missed.")

    log.status = MedicationLogStatus.missed.value
    db.commit()
    db.refresh(log)

    medication = db.query(Medication).filter(Medication.id == log.medication_id).first()
    _check_missed_streak(db, medication, log)

    return log


@router.get("/{patient_id}/medication/{medication_id}/adherence", response_model=MedicationAdherenceResponse)
def get_medication_adherence(
    patient_id: UUID,
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    _get_owned_medication(patient_id, medication_id, db)

    logs = db.query(MedicationLog).filter(MedicationLog.medication_id == medication_id).all()
    taken = sum(1 for l in logs if l.status == MedicationLogStatus.taken.value)
    missed = sum(1 for l in logs if l.status == MedicationLogStatus.missed.value)
    pending = sum(1 for l in logs if l.status == MedicationLogStatus.pending.value)
    completed = taken + missed
    adherence_percentage = round((taken / completed) * 100, 2) if completed else 0.0

    return MedicationAdherenceResponse(
        medication_id=medication_id, taken=taken, missed=missed, pending=pending,
        adherence_percentage=adherence_percentage,
    )
