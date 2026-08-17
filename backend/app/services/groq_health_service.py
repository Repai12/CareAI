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

GROQ_MODEL = "openai/gpt-oss-120b"
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


def _call_groq(prompt: str, history: Optional[list] = None) -> Optional[str]:
    client = _get_client()
    if client is None:
        return None
    messages = (history or []) + [{"role": "user", "content": prompt}]
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=4000,
            # gpt-oss is a reasoning model - "low" keeps its internal reasoning
            # budget small so the token allowance goes to the actual answer
            # instead of being silently exhausted on hidden reasoning tokens
            # (this is what caused empty responses on the 7-day diet plan).
            reasoning_effort="low",
        )
        content = response.choices[0].message.content
        return content if content else None
    except Exception as e:  # noqa: BLE001 - deliberately broad, mirrors ai_summary_service.py
        print(f"[Groq error] {e}")
        return None


def _extract_json(raw: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Feature 2: AI Health Report Analyzer
# ---------------------------------------------------------------------------

def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text.strip()


def summarize_health_report(extracted_text: str) -> dict:
    """Returns {summary, flagged_values}. flagged_values is a list of
    {label, value, status} for any specific numbers Groq calls out as
    outside a normal range - rendered as chips instead of buried in prose."""

    if not extracted_text:
        return {
            "summary": "Could not extract any readable text from this PDF - it may be a scanned image without a text layer.",
            "flagged_values": [],
        }

    prompt = f"""
You are explaining a medical report to an elderly patient's family in plain,
reassuring English. Respond ONLY with a JSON object with two keys:
- "summary": 5-8 plain-English sentences covering what the report is about,
  the key findings, and anything worth discussing with a doctor
- "flagged_values": a list of objects for any specific test values that are
  outside a normal range, each with "label" (e.g. "Cholesterol"), "value"
  (e.g. "240 mg/dL"), and "status" ("high" or "low"). Empty list if nothing
  is abnormal or no specific numeric values are present.

Do not invent values not present in the report below.

Report text:
{extracted_text[:12000]}
"""
    raw = _call_groq(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed:
            flags = parsed.get("flagged_values", [])
            if not isinstance(flags, list):
                flags = []
            return {"summary": parsed.get("summary", raw), "flagged_values": flags}
        return {"summary": raw, "flagged_values": []}

    return {
        "summary": (
            "Our AI summarizer is temporarily unavailable, so here is the raw extracted "
            f"text instead:\n\n{extracted_text[:2000]}"
        ),
        "flagged_values": [],
    }


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
        parsed = _extract_json(raw)
        if parsed:
            urgency = parsed.get("urgency", "monitor")
            if urgency not in ("normal", "monitor", "urgent", "emergency"):
                urgency = "monitor"
            return {"advice": parsed.get("advice", raw), "urgency": urgency}
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


def follow_up_symptoms(db: Session, patient_id, thread: list, message: str) -> dict:
    """Returns {advice, urgency} for a follow-up reply within an existing
    symptom-check thread. `thread` is the ordered list of prior SymptomLog
    rows (root first) so Groq has the full conversation, not just the new
    message in isolation."""

    vitals_context = _recent_vitals_context(db, patient_id)
    history_lines = []
    for entry in thread:
        history_lines.append(f"Patient: {entry.symptoms}")
        history_lines.append(f"Assistant: {entry.ai_response}")
    history_text = "\n".join(history_lines)

    prompt = f"""
You are continuing an ongoing symptom-check conversation with an elderly
patient (not a doctor - always recommend professional care for anything
serious). Respond ONLY with a JSON object with two keys:
- "urgency": one of "normal", "monitor", "urgent", "emergency"
- "advice": 2-4 plain-English sentences responding to the new detail below

Recent vitals:
{vitals_context}

Conversation so far:
{history_text}

Patient's new message:
{message}
"""
    raw = _call_groq(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed:
            urgency = parsed.get("urgency", "monitor")
            if urgency not in ("normal", "monitor", "urgent", "emergency"):
                urgency = "monitor"
            return {"advice": parsed.get("advice", raw), "urgency": urgency}
        return {"advice": raw, "urgency": _fallback_urgency(message)}

    urgency = _fallback_urgency(message)
    return {
        "advice": (
            "Our AI symptom checker is temporarily unavailable, so this is a basic "
            f"keyword-based check only (urgency: {urgency})."
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


def _stringify_plan(plan) -> str:
    """The prompt asks for `plan` as a formatted string, but the model
    sometimes returns a nested object instead (e.g. {"Day 1": {"Breakfast":
    ...}}) despite instructions - which would otherwise crash the DB insert
    (a Text column can't hold a dict). Render any shape into readable text."""
    if isinstance(plan, str):
        return plan
    if isinstance(plan, dict):
        lines = []
        for day, meals in plan.items():
            lines.append(f"## {day}")
            if isinstance(meals, dict):
                for meal, desc in meals.items():
                    lines.append(f"- {meal}: {desc}")
            elif isinstance(meals, list):
                lines.extend(f"- {item}" for item in meals)
            else:
                lines.append(f"- {meals}")
        return "\n".join(lines)
    if isinstance(plan, list):
        return "\n".join(str(item) for item in plan)
    return str(plan)


def generate_diet_plan(db: Session, patient_id) -> dict:
    """Returns {based_on_summary, plan, grocery_list}. The plan is generated
    from the patient's real vitals trend, not a generic template, and now
    spans a full week with a consolidated grocery list instead of a single
    day's meals."""

    trend_summary = _vitals_trend_summary(db, patient_id)
    prompt = f"""
You are a nutrition advisor for an elderly patient. Based on the vitals
trend below, respond ONLY with a JSON object with two keys:
- "plan": a SINGLE PLAIN TEXT STRING (not a nested object) containing a 7-day
  sample meal plan (breakfast, lunch, dinner, snack for each of Day 1 through
  Day 7), plus 2-3 short dietary tips at the end, tailored to what the trend
  suggests (e.g. lower sodium if BP looks high, lower-glycemic if sugar looks
  high). Keep it easy to follow for a home cook, in plain English, with line
  breaks and "Day N" headers written directly into the string.
- "grocery_list": a consolidated, deduplicated list of grocery item strings
  (ingredients only, e.g. "Oats", "Chicken breast", "Spinach") covering the
  whole week's plan. Group repeated ingredients into ONE entry - aim for a
  realistic weekly shopping list of at most 20-25 items, not one entry per
  meal.

Vitals trend:
{trend_summary}
"""
    raw = _call_groq(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed and parsed.get("plan"):
            grocery_list = parsed.get("grocery_list", [])
            if not isinstance(grocery_list, list):
                grocery_list = []
            # The model doesn't always respect the "~20-25 items" instruction
            # in the prompt - cap it server-side so the checklist UI stays usable.
            grocery_list = [str(item) for item in grocery_list][:30]
            return {"based_on_summary": trend_summary, "plan": _stringify_plan(parsed["plan"]), "grocery_list": grocery_list}
        return {"based_on_summary": trend_summary, "plan": raw, "grocery_list": []}

    plan_text = (
        "Our AI diet advisor is temporarily unavailable. General guidance in the "
        "meantime: favor whole grains, vegetables, and lean protein; limit added "
        "salt and sugar; stay hydrated. Please check back once the AI service is "
        "restored for a plan tailored to your recent vitals."
    )
    return {"based_on_summary": trend_summary, "plan": plan_text, "grocery_list": []}
