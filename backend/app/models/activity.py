"""
models/activity.py
---------------------
Module 1: "Activity tracking with trend dashboards" (README Features
table) - never built, no model, no router, no frontend. Same shape as
Mood Tracking (models/mood.py): multiple entries/day allowed, patient
self-reports, family/doctor get a read-only trend view. No wearable
integration exists in this app, so this is manual entry - the "trend
dashboard" is daily total minutes over time, not step-counting.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ActivityType(str, enum.Enum):
    walk = "walk"
    exercise = "exercise"
    chores = "chores"
    other = "other"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)  # ActivityType value
    duration_minutes = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
