"""
routers/wellness.py
----------------------
Module 2: Wellness Recommendation Engine (README Features table).
Grounded in the patient's real recent vitals/mood/activity, not a
generic tip list. Patient generates it for themselves; family/doctor
can view the latest read-only, same access bar as the diet plan.

Endpoints:
    POST /wellness/{patient_id}/generate  - generate fresh recommendations (patient, self only)
    GET  /wellness/{patient_id}/latest    - latest recommendations (patient self, or active-linked family/doctor)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus
from app.models.wellness import WellnessRecommendation
from app.schemas import WellnessRecommendationOut
from app.services.groq_health_service import generate_wellness_recommendations

router = APIRouter(prefix="/wellness", tags=["wellness"])


def _assert_can_view(patient_id: UUID, current_user: User, db: Session):
    if current_user.role == UserRole.patient.value:
        if current_user.id != patient_id:
            raise HTTPException(403, "Patients can only view their own wellness recommendations")
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
        raise HTTPException(403, "You do not have access to this patient's wellness recommendations")


@router.post("/{patient_id}/generate", response_model=WellnessRecommendationOut)
def generate_wellness(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.patient.value or current_user.id != patient_id:
        raise HTTPException(403, "Only the patient can generate their own wellness recommendations")

    result = generate_wellness_recommendations(db, patient_id)
    if result["recommendations"] is None:
        raise HTTPException(503, "Wellness recommendations are temporarily unavailable. Please try again shortly.")

    entry = WellnessRecommendation(
        patient_id=patient_id,
        based_on_summary=result["based_on_summary"],
        recommendations=result["recommendations"],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{patient_id}/latest", response_model=WellnessRecommendationOut | None)
def get_latest_wellness(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_can_view(patient_id, current_user, db)
    return (
        db.query(WellnessRecommendation)
        .filter(WellnessRecommendation.patient_id == patient_id)
        .order_by(WellnessRecommendation.created_at.desc())
        .first()
    )
