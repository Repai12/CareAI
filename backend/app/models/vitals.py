"""
models/vitals.py
------------------
OWNED BY MEMBER 1 (Mubasshira) - Vitals Logging, AI Health Report Analyzer,
AI Symptom Checker, AI Diet Advisor.

VitalsLog keeps its original class/table name and core columns so Member 4's
dashboard queries keep working. Everything below that is new: health_reports
(Feature 2), symptom_logs (Feature 3), and diet_plans/diet_logs (Feature 4 -
a persisted, trend-aware plan with adherence tracking instead of a one-off
Q&A call).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Float, DateTime, ForeignKey, String, LargeBinary, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class VitalsLog(Base):
    __tablename__ = "vitals_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blood_pressure = Column(String, nullable=False)   # e.g. "120/80"
    sugar_level = Column(Float, nullable=False)        # mg/dL
    heart_rate = Column(Float, nullable=False)         # bpm
    temperature = Column(Float, nullable=False)        # Celsius
    notes = Column(String, nullable=True)               # optional free-text ("felt dizzy after")
    logged_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", back_populates="vitals")


class HealthReport(Base):
    """Feature 2: AI Health Report Analyzer. Patient uploads a medical PDF,
    we extract its text and ask Gemini to summarize it in plain English."""

    __tablename__ = "health_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)      # original PDF bytes
    extracted_text = Column(Text, nullable=True)          # raw text pulled from the PDF
    ai_summary = Column(Text, nullable=True)               # Gemini's plain-English summary
    created_at = Column(DateTime, default=datetime.utcnow)


class UrgencyLevel(str, enum.Enum):
    normal = "normal"
    monitor = "monitor"
    urgent = "urgent"
    emergency = "emergency"


class SymptomLog(Base):
    """Feature 3: AI Symptom Checker. Unique twist vs. a plain chatbot call -
    the prompt is grounded in the patient's actual recent vitals so advice
    isn't generic, and Gemini is asked to return a structured urgency level.
    An "emergency" result auto-posts to the shared family Notification
    Center (Member 4's feed) instead of silently sitting in a log."""

    __tablename__ = "symptom_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    symptoms = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    urgency = Column(String, nullable=False, default=UrgencyLevel.normal.value)
    escalated = Column(Boolean, default=False)  # True if this triggered a family notification
    created_at = Column(DateTime, default=datetime.utcnow)


class DietPlan(Base):
    """Feature 4: AI Diet Advisor. Unique twist vs. a plain chatbot call -
    the plan is generated from the patient's actual vitals trend (average
    sugar/BP over the last 2 weeks) so it's a genuine recommendation, not a
    generic diet list, and it's persisted so adherence can be tracked
    against it (see DietLog) instead of being a throwaway response."""

    __tablename__ = "diet_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    based_on_summary = Column(Text, nullable=False)   # the vitals-trend context fed to Gemini
    ai_plan = Column(Text, nullable=False)             # structured plan text
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("DietLog", back_populates="plan", cascade="all, delete-orphan")


class DietLog(Base):
    """Daily adherence check-in against an active DietPlan."""

    __tablename__ = "diet_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("diet_plans.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    followed = Column(Boolean, nullable=False)
    note = Column(String, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("DietPlan", back_populates="logs")
