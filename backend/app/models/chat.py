"""
models/chat.py
-----------------
Module 3: Family Chat (README Features table, explicitly named in the
Tech Stack table: "Real-time: WebSockets (family/doctor chat)"). The
chat "room" is scoped to a patient - their whole care circle (the
patient themselves plus any actively-linked family/doctor) shares one
thread, same scoping as every other per-patient feature in this app.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sender_name = Column(Text, nullable=False)
    sender_role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_chat_messages_patient_created", "patient_id", "created_at"),
    )
