import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SafetyCheckin(Base):
    __tablename__ = "safety_checkins"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    checked_in_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    is_checked_in = Column(
        Boolean,
        default=True,
        nullable=False
    )
