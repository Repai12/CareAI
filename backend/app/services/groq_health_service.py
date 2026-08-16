"""
services/groq_health_service.py
------------------------------------
OWNED BY MEMBER 1 (Mubasshira) - Groq (Llama 3.3 70B) integration backing
Features 2-4 (AI Health Report Analyzer, AI Symptom Checker, AI Diet
Advisor). Free tier, OpenAI-compatible chat completions API.

New file - doesn't touch Member 4's services/ai_summary_service.py (which
uses Gemini for its own Doctor Summary feature).

Same defensive pattern used elsewhere in this codebase: never let an AI
provider failure (missing key, timeout, quota) crash the request. Every
public function here falls back to a clearly-labelled result instead.
"""

import json
import re
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

from groq import Groq
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.config import settings
from app.models.vitals import VitalsLog

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TIMEOUT_SECONDS = 15

_client: Optional[Groq] = None


def _get_client() -> Optional[Groq]:
    """Lazily builds the Groq client. Returns None (instead of raising) if
    no API key is set, so callers can fall back cleanly."""
    global _client
    if not settings.GROQ_API_KEY:
        return None
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS)
    return _client


def _call_groq(prompt: str) -> Optional[str]:
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:  # noqa: BLE001 - deliberately broad, mirrors ai_summary_service.py
        print(f"[Groq error] {e}")
        return None


# ---------------------------------------------------------------------------
# Feature 2: AI Health Report Analyzer
# ---------------------------------------------------------------------------

def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text.strip()


def summarize_health_report(extracted_text: str) -> str:
    if not extracted_text:
        return "Could not extract any readable text from this PDF - it may be a scanned image without a text layer."

    prompt = f"""
You are explaining a medical report to an elderly patient's family in plain,
reassuring English (no jargon, 5-8 sentences). Cover: what the report is
about, the key numbers/findings, and anything that looks abnormal or worth
discussing with a doctor. Do not invent values not present below.

Report text:
{extracted_text[:12000]}
"""
    result = _call_groq(prompt)
    if result:
        return result
    return (
        "Our AI summarizer is temporarily unavailable, so here is the raw extracted "
        f"text instead:\n\n{extracted_text[:2000]}"
    )


# ---------------------------------------------------------------------------
# Feature 3: AI Symptom Checker (context-aware + urgency triage)
# ---------------------------------------------------------------------------

_URGENCY_KEYWORDS = {
    "emergency": ["chest pain", "can't breathe", "cannot breathe", "unconscious", "severe bleeding", "stroke", "seizure"],
    "urgent": ["fever", "vomiting", "dizziness", "shortness of breath", "swelling"],
}


def _recent_vitals_context(db: Session, patient_id) -> str:
    recent = (
        db.query(VitalsLog)
        .filter(VitalsLog.patient_id == patient_id)
        .order_by(VitalsLog.logged_at.desc())
        .limit(5)
        .all()
    )
    if not recent:
        return "No recent vitals on file."
    lines = [
        f"- {v.logged_at.strftime('%d %b')}: BP {v.blood_pressure}, sugar {v.sugar_level} mg/dL, "
        f"HR {v.heart_rate} bpm, temp {v.temperature}°C"
        for v in recent
    ]
    return "\n".join(lines)


def _fallback_urgency(symptoms: str) -> str:
    lowered = symptoms.lower()
    if any(k in lowered for k in _URGENCY_KEYWORDS["emergency"]):
        return "emergency"
    if any(k in lowered for k in _URGENCY_KEYWORDS["urgent"]):
        return "urgent"
    return "monitor"


def check_symptoms(db: Session, patient_id, symptoms: str) -> dict:
    """Returns {advice, urgency}. Grounds the prompt in the patient's actual
    recent vitals so the advice is contextual, and asks Groq to classify
    urgency as one of normal/monitor/urgent/emergency so the caller can
    decide whether to escalate to the family notification feed."""

    vitals_context = _recent_vitals_context(db, patient_id)
    prompt = f"""
You are a cautious triage assistant for an elderly patient (not a doctor -
always recommend professional care for anything serious). Given the
patient's recent vitals and their described symptoms, respond ONLY with a
JSON object with two keys:
- "urgency": one of "normal", "monitor", "urgent", "emergency"
- "advice": 2-4 plain-English sentences with possible causes and what to do

Recent vitals:
{vitals_context}

Reported symptoms:
{symptoms}
"""
    raw = _call_groq(prompt)
    if raw:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                urgency = parsed.get("urgency", "monitor")
                if urgency not in ("normal", "monitor", "urgent", "emergency"):
                    urgency = "monitor"
                return {"advice": parsed.get("advice", raw), "urgency": urgency}
            except json.JSONDecodeError:
                pass
        return {"advice": raw, "urgency": _fallback_urgency(symptoms)}

    urgency = _fallback_urgency(symptoms)
    return {
        "advice": (
            "Our AI symptom checker is temporarily unavailable, so this is a basic "
            f"keyword-based check only (urgency: {urgency}). Please contact a doctor "
            "if symptoms are severe or worsening."
        ),
        "urgency": urgency,
    }


# ---------------------------------------------------------------------------
# Feature 4: AI Diet Advisor (trend-aware plan + adherence tracking)
# ---------------------------------------------------------------------------

def _vitals_trend_summary(db: Session, patient_id) -> str:
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    recent = (
        db.query(VitalsLog)
        .filter(VitalsLog.patient_id == patient_id, VitalsLog.logged_at >= two_weeks_ago)
        .order_by(VitalsLog.logged_at)
        .all()
    )
    if not recent:
        return "No vitals logged in the last 14 days - use general healthy-aging guidance."

    avg_sugar = sum(v.sugar_level for v in recent) / len(recent)
    avg_hr = sum(v.heart_rate for v in recent) / len(recent)
    systolics = []
    for v in recent:
        try:
            systolics.append(int(v.blood_pressure.split("/")[0]))
        except (ValueError, IndexError):
            continue
    avg_systolic = sum(systolics) / len(systolics) if systolics else None

    parts = [f"{len(recent)} readings over the last 14 days.", f"Average sugar level: {avg_sugar:.0f} mg/dL."]
    if avg_systolic:
        parts.append(f"Average systolic BP: {avg_systolic:.0f}.")
    parts.append(f"Average heart rate: {avg_hr:.0f} bpm.")
    return " ".join(parts)


def generate_diet_plan(db: Session, patient_id) -> dict:
    """Returns {based_on_summary, plan}. The plan is generated from the
    patient's real vitals trend, not a generic template."""

    trend_summary = _vitals_trend_summary(db, patient_id)
    prompt = f"""
You are a nutrition advisor for an elderly patient. Based on the vitals
trend below, write a simple 1-day sample meal plan (breakfast, lunch,
dinner, snack) plus 2-3 short dietary tips, tailored to what the trend
suggests (e.g. lower sodium if BP looks high, lower-glycemic if sugar looks
high). Keep it easy to follow for a home cook, in plain English.

Vitals trend:
{trend_summary}
"""
    plan_text = _call_groq(prompt)
    if not plan_text:
        plan_text = (
            "Our AI diet advisor is temporarily unavailable. General guidance in the "
            "meantime: favor whole grains, vegetables, and lean protein; limit added "
            "salt and sugar; stay hydrated. Please check back once the AI service is "
            "restored for a plan tailored to your recent vitals."
        )
    return {"based_on_summary": trend_summary, "plan": plan_text}
