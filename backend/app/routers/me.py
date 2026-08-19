"""
routers/me.py
--------------
OWNED BY MEMBER 4 (Repai). Tells the frontend which patient dashboard(s)
the logged-in user can see, right after login - no manual patient ID
entry needed anywhere in the app.

Also owns the care_links connection-management endpoints (README S4.4):
listing your own connections (with status), and - patient-only - the
two-sided approve/decline/revoke actions and adjusting a viewer's
permission level. Everything here is scoped to `current_user`; nobody
can act on a connection they aren't a party to.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission
from app.models.notification import NotificationCategory
from app.services.notification_service import create_notification
from app.schemas import UserBase, CareLinkOut, CareLinkPermissionUpdate

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/patients", response_model=list[UserBase])
def get_my_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.patient.value:
        return [current_user]

    links = (
        db.query(CareLink)
        .filter(CareLink.viewer_id == current_user.id, CareLink.status == CareLinkStatus.active.value)
        .all()
    )
    patient_ids = [link.patient_id for link in links]
    if not patient_ids:
        return []

    return db.query(User).filter(User.id.in_(patient_ids)).all()


def _to_out(link: CareLink, patient: User, viewer: User) -> CareLinkOut:
    return CareLinkOut(
        id=link.id,
        patient_id=link.patient_id,
        patient_name=patient.name,
        viewer_id=link.viewer_id,
        viewer_name=viewer.name,
        link_role=link.link_role,
        relationship_label=link.relationship_label,
        permission_level=link.permission_level,
        status=link.status,
        created_at=link.created_at,
        responded_at=link.responded_at,
        revoked_at=link.revoked_at,
    )


@router.get("/connections", response_model=list[CareLinkOut])
def get_my_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Every care_links row `current_user` is a party to, any status - as
    the patient, this is /patient/connections (README S4.4); as a
    family/doctor viewer, this is how they see a still-pending request
    they sent, or something the patient later revoked.
    """
    if current_user.role == UserRole.patient.value:
        links = db.query(CareLink).filter(CareLink.patient_id == current_user.id).all()
    else:
        links = db.query(CareLink).filter(CareLink.viewer_id == current_user.id).all()

    if not links:
        return []

    user_ids = {l.patient_id for l in links} | {l.viewer_id for l in links}
    users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}
    return [_to_out(l, users_by_id[l.patient_id], users_by_id[l.viewer_id]) for l in links]


def _get_pending_link_as_patient(link_id: uuid.UUID, current_user: User, db: Session) -> CareLink:
    if current_user.role != UserRole.patient.value:
        raise HTTPException(403, "Only the patient can respond to a connection request")
    link = db.query(CareLink).filter(CareLink.id == link_id, CareLink.patient_id == current_user.id).first()
    if not link:
        raise HTTPException(404, "Connection request not found")
    if link.status != CareLinkStatus.pending.value:
        raise HTTPException(400, f"This request is already {link.status}, not pending")
    return link


@router.post("/connections/{link_id}/approve", response_model=CareLinkOut)
def approve_connection(
    link_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_pending_link_as_patient(link_id, current_user, db)
    link.status = CareLinkStatus.active.value
    link.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(link)

    viewer = db.query(User).filter(User.id == link.viewer_id).first()
    create_notification(
        db,
        patient_id=current_user.id,
        event_type="CONNECTION_APPROVED",
        title="Connection approved",
        message=f"You approved {viewer.name} as your {link.link_role}.",
        category=NotificationCategory.connection,
    )
    return _to_out(link, current_user, viewer)


@router.post("/connections/{link_id}/decline", response_model=CareLinkOut)
def decline_connection(
    link_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_pending_link_as_patient(link_id, current_user, db)
    link.status = CareLinkStatus.declined.value
    link.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(link)

    viewer = db.query(User).filter(User.id == link.viewer_id).first()
    return _to_out(link, current_user, viewer)


@router.post("/connections/{link_id}/revoke", response_model=CareLinkOut)
def revoke_connection(
    link_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Patient-only (README S4.4). Sets status=revoked rather than deleting
    the row, so there's still an audit trail of who had access and when -
    the viewer's dashboard just stops returning this patient going
    forward; notifications they already received aren't retroactively
    hidden.
    """
    if current_user.role != UserRole.patient.value:
        raise HTTPException(403, "Only the patient can revoke a connection")
    link = db.query(CareLink).filter(CareLink.id == link_id, CareLink.patient_id == current_user.id).first()
    if not link:
        raise HTTPException(404, "Connection not found")
    if link.status != CareLinkStatus.active.value:
        raise HTTPException(400, f"This connection is {link.status}, not active")

    link.status = CareLinkStatus.revoked.value
    link.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(link)

    viewer = db.query(User).filter(User.id == link.viewer_id).first()
    return _to_out(link, current_user, viewer)


@router.post("/connections/{link_id}/permission", response_model=CareLinkOut)
def update_connection_permission(
    link_id: uuid.UUID,
    payload: CareLinkPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Patient-only: upgrade/downgrade a viewer between view_only and view_and_manage (README S4.3)."""
    if current_user.role != UserRole.patient.value:
        raise HTTPException(403, "Only the patient can change a connection's permission level")
    if payload.permission_level not in (p.value for p in CareLinkPermission):
        raise HTTPException(400, "permission_level must be 'view_only' or 'view_and_manage'")

    link = db.query(CareLink).filter(CareLink.id == link_id, CareLink.patient_id == current_user.id).first()
    if not link:
        raise HTTPException(404, "Connection not found")
    if link.status != CareLinkStatus.active.value:
        raise HTTPException(400, "Only an active connection's permission can be changed")

    link.permission_level = payload.permission_level
    db.commit()
    db.refresh(link)

    viewer = db.query(User).filter(User.id == link.viewer_id).first()
    return _to_out(link, current_user, viewer)
