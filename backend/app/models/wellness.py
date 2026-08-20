"""
models/wellness.py
---------------------
Module 2: "Wellness recommendation engine" (README Features table,
listed as its own item separate from "nutrition planner" - Diet
Advisor already covers nutrition, this is the broader lifestyle
counterpart: sleep/activity/stress/social tips, not meal plans). Never
built - zero code anywhere, confirmed by grep.

Grounded in the patient's real recent vitals, mood, and activity trends
(the three self-reported logs this app already has) rather than being
a generic tip list, same "real data, not generic" principle the diet
plan/symptom checker already use. Persisted so there's a history, same
reasoning as DietPlan - not a throwaway call.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class WellnessRecommendation(Base):
    __tablename__ = "wellness_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    based_on_summary = Column(Text, nullable=False)  # the vitals/mood/activity context fed to Groq
    recommendations = Column(Text, nullable=False)    # AI-generated tips, plain text
    created_at = Column(DateTime, default=datetime.utcnow)
