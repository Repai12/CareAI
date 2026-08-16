import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class FallIncident(Base):
    __tablename__ = "fall_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    severity = Column(String(30), nullable=False)
    details = Column(Text, nullable=True)

    occurred_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )