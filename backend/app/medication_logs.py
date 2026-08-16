from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Medication, MedicationLog
from .schemas import (
    MedicationLogCreate,
    MedicationLogResponse,
    MedicationAdherenceResponse,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/medication-logs",
    tags=["Medication Logs"]
)


# ============================================================
# BANGLADESH TIMEZONE
# ============================================================

BANGLADESH_TZ = ZoneInfo("Asia/Dhaka")


# ============================================================
# HELPER — CURRENT BANGLADESH TIME
# ============================================================

def get_current_bangladesh_datetime() -> datetime:
    return datetime.now(BANGLADESH_TZ)


# ============================================================
# HELPER — MAKE DATETIME TIMEZONE-AWARE
# ============================================================

def make_bangladesh_datetime(dt: datetime) -> datetime:

    # If the incoming datetime already has timezone
    # information, convert it to Bangladesh time.

    if dt.tzinfo is not None:

        return dt.astimezone(BANGLADESH_TZ)

    # If it is a naive datetime, assume it was entered
    # in Bangladesh time.

    return dt.replace(
        tzinfo=BANGLADESH_TZ
    )


# ============================================================
# CREATE MEDICATION REMINDER
# ============================================================

@router.post(
    "/",
    response_model=MedicationLogResponse
)
def create_medication_log(
    medication_log: MedicationLogCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Check that the medication exists
    # --------------------------------------------------------

    medication = (
        db.query(Medication)
        .filter(
            Medication.id
            == medication_log.medication_id
        )
        .first()
    )

    if medication is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found."
        )

    # --------------------------------------------------------
    # 2. Convert scheduled time to Bangladesh time
    # --------------------------------------------------------

    scheduled_at = make_bangladesh_datetime(
        medication_log.scheduled_at
    )

    current_datetime = (
        get_current_bangladesh_datetime()
    )

    # --------------------------------------------------------
    # 3. Prevent past medication schedules
    # --------------------------------------------------------

    if scheduled_at <= current_datetime:

        raise HTTPException(
            status_code=400,
            detail=(
                "Medication reminder cannot be "
                "scheduled in the past."
            )
        )

    # --------------------------------------------------------
    # 4. Check for duplicate reminder
    # --------------------------------------------------------

    existing_log = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.medication_id
            == medication_log.medication_id,

            MedicationLog.scheduled_at
            == medication_log.scheduled_at
        )
        .first()
    )

    if existing_log is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "A medication reminder already exists "
                "for this date and time."
            )
        )

    # --------------------------------------------------------
    # 5. Create medication log
    # --------------------------------------------------------

    new_log = MedicationLog(
        medication_id=medication_log.medication_id,
        scheduled_at=scheduled_at,
        taken_at=None,
        status="pending"
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


# ============================================================
# GET ALL MEDICATION LOGS
# ============================================================

@router.get(
    "/",
    response_model=list[MedicationLogResponse]
)
def get_medication_logs(
    db: Session = Depends(get_db)
):

    logs = (
        db.query(MedicationLog)
        .order_by(
            MedicationLog.scheduled_at.asc()
        )
        .all()
    )

    return logs


# ============================================================
# GET LOGS FOR ONE MEDICATION
# ============================================================

@router.get(
    "/medication/{medication_id}",
    response_model=list[MedicationLogResponse]
)
def get_medication_logs_for_medication(
    medication_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check medication exists
    # --------------------------------------------------------

    medication = (
        db.query(Medication)
        .filter(
            Medication.id == medication_id
        )
        .first()
    )

    if medication is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found."
        )

    # --------------------------------------------------------
    # Get medication logs
    # --------------------------------------------------------

    logs = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.medication_id
            == medication_id
        )
        .order_by(
            MedicationLog.scheduled_at.asc()
        )
        .all()
    )

    return logs


# ============================================================
# MARK MEDICATION AS TAKEN
# ============================================================

@router.put(
    "/{log_id}/taken",
    response_model=MedicationLogResponse
)
def mark_medication_taken(
    log_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find medication log
    # --------------------------------------------------------

    log = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.id == log_id
        )
        .first()
    )

    if log is None:

        raise HTTPException(
            status_code=404,
            detail="Medication reminder not found."
        )

    # --------------------------------------------------------
    # 2. Prevent taking an already completed reminder
    # --------------------------------------------------------

    if log.status == "taken":

        raise HTTPException(
            status_code=400,
            detail=(
                "This medication reminder has "
                "already been marked as taken."
            )
        )

    # --------------------------------------------------------
    # 3. Mark as taken
    # --------------------------------------------------------

    log.taken_at = (
        get_current_bangladesh_datetime()
    )

    log.status = "taken"

    db.commit()
    db.refresh(log)

    return log


# ============================================================
# MARK MEDICATION AS MISSED
# ============================================================

@router.put(
    "/{log_id}/missed",
    response_model=MedicationLogResponse
)
def mark_medication_missed(
    log_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find medication log
    # --------------------------------------------------------

    log = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.id == log_id
        )
        .first()
    )

    if log is None:

        raise HTTPException(
            status_code=404,
            detail="Medication reminder not found."
        )

    # --------------------------------------------------------
    # 2. Don't overwrite completed reminders
    # --------------------------------------------------------

    if log.status == "taken":

        raise HTTPException(
            status_code=400,
            detail=(
                "A medication already marked as taken "
                "cannot be marked as missed."
            )
        )

    # --------------------------------------------------------
    # 3. Mark as missed
    # --------------------------------------------------------

    log.status = "missed"

    db.commit()
    db.refresh(log)

    return log


# ============================================================
# MEDICATION ADHERENCE
# ============================================================

@router.get(
    "/medication/{medication_id}/adherence",
    response_model=MedicationAdherenceResponse
)
def get_medication_adherence(
    medication_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Check medication exists
    # --------------------------------------------------------

    medication = (
        db.query(Medication)
        .filter(
            Medication.id == medication_id
        )
        .first()
    )

    if medication is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found."
        )

    # --------------------------------------------------------
    # 2. Get all logs
    # --------------------------------------------------------

    logs = (
        db.query(MedicationLog)
        .filter(
            MedicationLog.medication_id
            == medication_id
        )
        .all()
    )

    # --------------------------------------------------------
    # 3. Count statuses
    # --------------------------------------------------------

    taken = sum(
        1
        for log in logs
        if log.status == "taken"
    )

    missed = sum(
        1
        for log in logs
        if log.status == "missed"
    )

    pending = sum(
        1
        for log in logs
        if log.status == "pending"
    )

    # --------------------------------------------------------
    # 4. Calculate adherence percentage
    # --------------------------------------------------------

    completed = taken + missed

    if completed == 0:

        adherence_percentage = 0.0

    else:

        adherence_percentage = (
            taken / completed
        ) * 100

    # --------------------------------------------------------
    # 5. Return adherence information
    # --------------------------------------------------------

    return MedicationAdherenceResponse(
        medication_id=medication_id,
        taken=taken,
        missed=missed,
        pending=pending,
        adherence_percentage=round(
            adherence_percentage,
            2
        )
    )