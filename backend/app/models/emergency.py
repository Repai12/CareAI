import uuid

from sqlalchemy import Column, String, Integer, ForeignKey
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