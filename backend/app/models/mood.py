"""
models/mood.py
-----------------
Module 1: Mood Tracking. README's Features table lists this alongside
activity tracking/trend dashboards but nothing was ever built - no model,
no router, no frontend. Multiple logs per day are allowed on purpose (a
real user logs mood more than once a day); the dashboard/trend view is
responsible for summarizing, not this table.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class MoodLevel(str, enum.Enum):
    great = "great"
    good = "good"
    okay = "okay"
    low = "low"
    bad = "bad"


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mood = Column(String, nullable=False)  # MoodLevel value
    note = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
