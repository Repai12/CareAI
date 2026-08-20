"""
models/companion.py
----------------------
Module 3: Dual-Persona AI Companion (README Features table). No detailed
spec exists for what the two personas are - picked to match the
product's own stated purpose (README overview: reducing isolation,
keeping patients safe without constant phone calls):

- "companion": warm, casual, conversational - targets loneliness.
- "coach": upbeat and practical - nudges medication adherence/activity,
  lightly grounded in the patient's own recent vitals trend.

Each persona keeps its own separate message thread (not a shared one) so
switching personas doesn't dump one persona's casual chat into the
other's context out of place.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CompanionPersona(str, enum.Enum):
    companion = "companion"
    coach = "coach"


class CompanionRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class CompanionMessage(Base):
    __tablename__ = "companion_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    persona = Column(Text, nullable=False)  # CompanionPersona value
    role = Column(Text, nullable=False)  # CompanionRole value
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
