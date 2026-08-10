from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from . import crud
from . import schemas


# ============================================================
# MEDICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/medications",
    tags=["Medications"]
)


@router.post(
    "/",
    response_model=schemas.MedicationResponse
)
def add_medication(
    medication: schemas.MedicationCreate,
    db: Session = Depends(get_db)
):
    return crud.create_medication(
        db,
        medication
    )


@router.get(
    "/",
    response_model=list[schemas.MedicationResponse]
)
def read_medications(
    db: Session = Depends(get_db)
):
    return crud.get_medications(db)


@router.get(
    "/{medication_id}",
    response_model=schemas.MedicationResponse
)
def read_medication(
    medication_id: int,
    db: Session = Depends(get_db)
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

    return medication


@router.put(
    "/{medication_id}",
    response_model=schemas.MedicationResponse
)
def edit_medication(
    medication_id: int,
    medication: schemas.MedicationCreate,
    db: Session = Depends(get_db)
):

    updated = crud.update_medication(
        db,
        medication_id,
        medication
    )

    if updated is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found"
        )

    return updated


@router.delete(
    "/{medication_id}"
)
def remove_medication(
    medication_id: int,
    db: Session = Depends(get_db)
):

    medication = crud.delete_medication(
        db,
        medication_id
    )

    if medication is None:

        raise HTTPException(
            status_code=404,
            detail="Medication not found"
        )

    return {
        "message":
            "Medication deleted successfully"
    }