"""
models/patient_qa.py
-----------------------
Module 3: AI Patient History Q&A (README Features table - "Doctor ...
uses AI to analyze reports, answers patient-history questions"). A
doctor-facing tool, not patient/family-facing, same split as the
existing doctor-only AI Summary Email feature (routers/ai_summary.py).

Persisted (not a throwaway call) so a doctor's past Q&A for a patient is
a reusable record - same reasoning SymptomLog/DietPlan already use.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PatientQuestion(Base):
    __tablename__ = "patient_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
