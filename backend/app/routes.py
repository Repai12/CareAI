"""
routes.py
---------
OWNED BY MEMBER 2 (Afifa) - Medication CRUD.

Patient-scoped and role-aware:
- GET  /medications/patient/{patient_id} - view (patient self, linked
  family, or linked doctor) - returns current AND past medications.
- POST/PUT/DELETE - patient (own) or a linked doctor can write; family
  is view-only, matching the read/write split used for vitals/emergency
  elsewhere in this app.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import get_current_user
from .models.user import User, UserRole, PatientLink
from . import crud
from . import schemas


router = APIRouter(
    prefix="/medications",
    tags=["Medications"]
)


def _assert_can_view(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own medications")
        return
    link = (
        db.query(PatientLink)
        .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
        .first()
    )
    if not link:
        raise HTTPException(403, "You do not have access to this patient's medications")


def _assert_can_edit(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only manage their own medications")
        return
    if current_user.role == UserRole.doctor.value:
        link = (
            db.query(PatientLink)
            .filter(PatientLink.patient_id == patient_id, PatientLink.viewer_id == current_user.id)
            .first()
        )
        if not link:
            raise HTTPException(403, "You are not linked to this patient")
        return
    raise HTTPException(403, "Family members can view medications but not add or edit them")


@router.post(
    "/",
    response_model=schemas.MedicationResponse
)
def add_medication(
    medication: schemas.MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_edit(medication.patient_id, current_user, db)
    return crud.create_medication(
        db,
        medication
    )


@router.get(
    "/patient/{patient_id}",
    response_model=list[schemas.MedicationResponse]
)
def read_medications_for_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return crud.get_medications(db, patient_id)


@router.get(
    "/{medication_id}",
    response_model=schemas.MedicationResponse
)
def read_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    medication = crud.get_medication(
        db,
        medication_id
    )

    if medication is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found"
        )

    if medication.patient_id:
        _assert_can_view(medication.patient_id, current_user, db)

    return medication


@router.put(
    "/{medication_id}",
    response_model=schemas.MedicationResponse
)
def edit_medication(
    medication_id: UUID,
    medication: schemas.MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = crud.get_medication(db, medication_id)
    if existing is None:
        raise HTTPException(404, "Medication not found")
    if existing.patient_id:
        _assert_can_edit(existing.patient_id, current_user, db)

    updated = crud.update_medication(
        db,
        medication_id,
        medication
    )

    return updated


@router.delete(
    "/{medication_id}"
)
def remove_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = crud.get_medication(db, medication_id)
    if existing is None:
        raise HTTPException(404, "Medication not found")
    if existing.patient_id:
        _assert_can_edit(existing.patient_id, current_user, db)

    crud.delete_medication(
        db,
        medication_id
    )

    return {
        "message":
            "Medication deleted successfully"
    }
