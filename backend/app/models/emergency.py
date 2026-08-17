import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as db_relationship

from app.database import Base


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    relationship = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False, default=1)

    user = db_relationship(
        "User",
        back_populates="emergency_contacts"
    )


# NOTE (Mubasshira): added below - the merged Module 3 check-in PR (#16)
# referenced this class from routers/emergency.py and
# services/safety_checkin_service.py but never actually defined it, which
# broke backend startup for everyone. Fields inferred from that existing
# usage (SafetyCheckin(user_id=...), .checked_in_at, .is_checked_in).
# Faisal - please verify this matches what you intended.
