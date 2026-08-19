"""
routers/medications.py
------------------------
OWNED BY MEMBER 2 (Afifa) - Medication Management (README S6.2/S8.4).

Real patient-scoped CRUD. Every route re-verifies the caller's access
the same way every other router in the app does (patient acting on
themselves, or an active care_link with view_and_manage permission to
create/edit/delete - view_only viewers can still list/read).
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from app.models.medication import Medication
from app.schemas import MedicationCreate, MedicationUpdate, MedicationResponse

router = APIRouter(prefix="/medications", tags=["medications"])


def _assert_can_view(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own medications")
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
        raise HTTPException(403, "You do not have access to this patient's medications")


def _assert_can_manage(patient_id: uuid.UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only manage their own medications")
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
        raise HTTPException(403, "You do not have permission to manage this patient's medications")


@router.get("/{patient_id}", response_model=List[MedicationResponse])
def list_medications(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(Medication)
        .filter(Medication.patient_id == patient_id)
        .order_by(Medication.start_date.desc().nullslast())
        .all()
    )


@router.post("/{patient_id}", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    patient_id: uuid.UUID,
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    if payload.end_date and payload.start_date and payload.end_date < payload.start_date:
        raise HTTPException(400, "End date cannot be before start date")

    med = Medication(patient_id=patient_id, **payload.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.put("/{patient_id}/{medication_id}", response_model=MedicationResponse)
def update_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    payload: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    med = db.query(Medication).filter(Medication.id == medication_id, Medication.patient_id == patient_id).first()
    if not med:
        raise HTTPException(404, "Medication not found")

    updates = payload.model_dump(exclude_unset=True)
    new_start = updates.get("start_date", med.start_date)
    new_end = updates.get("end_date", med.end_date)
    if new_end and new_start and new_end < new_start:
        raise HTTPException(400, "End date cannot be before start date")

    for field, value in updates.items():
        setattr(med, field, value)

    db.commit()
    db.refresh(med)
    return med


@router.delete("/{patient_id}/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_manage(patient_id, current_user, db)
    med = db.query(Medication).filter(Medication.id == medication_id, Medication.patient_id == patient_id).first()
    if not med:
        raise HTTPException(404, "Medication not found")

    db.delete(med)
    db.commit()
    return None
