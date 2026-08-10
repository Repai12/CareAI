"""
me.py
-----
Small helper endpoint so the frontend can figure out, right after login,
which patient dashboard(s) the logged-in user is allowed to see -
without the user having to know or type any patient ID manually.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserRole, PatientLink
from app.schemas import UserBase

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/patients", response_model=list[UserBase])
def get_my_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.patient:
        return [current_user]

    links = db.query(PatientLink).filter(PatientLink.viewer_id == current_user.id).all()
    patient_ids = [link.patient_id for link in links]
    if not patient_ids:
        return []

    patients = db.query(User).filter(User.id.in_(patient_ids)).all()
    return patients