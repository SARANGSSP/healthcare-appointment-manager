"""
LLM Services module (Build Plan Chunks 12 & 13 / Design Document §9.2, §10).
Uses Gemini API / Groq API to generate JSON-constrained pre-visit urgency triage and post-visit patient summaries.

M1 fix: API keys are now read via current_app.config (with os.environ fallback)
        rather than raw os.environ.get() calls throughout.
"""
import json
import os
import re
import urllib.request
import urllib.error

try:
    from flask import current_app as _flask_app
except ImportError:
    _flask_app = None


def _get_api_key(name: str) -> str:
    """Read an API key from Flask app config (M1 fix), falling back to os.environ."""
    try:
        val = _flask_app.config.get(name) if _flask_app else None
        return val or os.environ.get(name, "")
    except RuntimeError:
        # No active app context (e.g. running in a test or standalone script)
        return os.environ.get(name, "")


# Structured JSON prompt templates (Design Document §10)
PRE_VISIT_PROMPT = """You are a medical triage assistant. Analyze these patient symptoms and respond ONLY with a valid JSON object.
Do not include any markdown formatting, backticks, or extra text.

JSON Schema:
{
  "urgency": "Low" | "Medium" | "High",
  "chief_complaint": "string concise 1-sentence summary",
  "suggested_questions": ["question 1 for doctor", "question 2 for doctor", "question 3 for doctor"]
}

Patient Symptoms:
<symptoms>
{symptoms}
</symptoms>
"""

POST_VISIT_PROMPT = """You are a medical assistant converting clinical notes into patient-friendly instructions.
Respond ONLY with a valid JSON object. Do not include markdown formatting or backticks.

JSON Schema:
{
  "patient_summary": "plain-language 2-sentence summary for the patient",
  "medication_instructions": [
    {
      "medication_name": "string",
      "schedule": "string e.g. Twice daily after meals for 5 days",
      "advice": "string"
    }
  ],
  "follow_up": "string e.g. Return in 2 weeks if symptoms persist"
}

Clinical Notes & Prescriptions:
<notes>
{notes}
</notes>
"""


def _extract_json(text):
    """Clean markdown code blocks and parse JSON safely."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback regex search for { ... }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def generate_pre_visit_summary(symptoms_text):
    """
    Generates pre-visit urgency triage JSON (Low/Medium/High, chief complaint, 3 suggested questions).
    Returns dict on success or None on failure (B3).
    """
    if not symptoms_text or not symptoms_text.strip():
        return None

    api_key = _get_api_key("GEMINI_API_KEY") or _get_api_key("GROQ_API_KEY")
    if not api_key:
        return None

    prompt = PRE_VISIT_PROMPT.replace("<symptoms>", f"<symptoms>\n{symptoms_text.strip()}\n</symptoms>")

    try:
        if _get_api_key("GEMINI_API_KEY"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = _extract_json(text)
                if parsed and "urgency" in parsed:
                    return parsed
        elif _get_api_key("GROQ_API_KEY"):
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": "llama-3.3-70b-versatile",
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                parsed = _extract_json(text)
                if parsed and "urgency" in parsed:
                    return parsed
    except Exception:
        pass

    return None


def generate_post_visit_summary(clinical_notes, prescriptions=None):
    """
    Generates post-visit patient-friendly rewrite and medication instructions JSON.
    """
    if not clinical_notes or not clinical_notes.strip():
        return None

    full_text = f"Notes: {clinical_notes.strip()}\n"
    if prescriptions:
        full_text += f"Prescriptions: {json.dumps(prescriptions)}"

    api_key = _get_api_key("GEMINI_API_KEY") or _get_api_key("GROQ_API_KEY")
    if not api_key:
        return None

    prompt = POST_VISIT_PROMPT.replace("<notes>", f"<notes>\n{full_text}\n</notes>")

    try:
        if _get_api_key("GEMINI_API_KEY"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = _extract_json(text)
                if parsed and "patient_summary" in parsed:
                    return parsed
    except Exception:
        pass

    return None


def _fallback_pre_visit(symptoms_text):
    """Determines clinical signal rule-based triage when offline/testing."""
    lower = symptoms_text.lower()
    urgency = "Low"
    if any(w in lower for w in ["chest pain", "breath", "severe", "bleeding", "unconscious"]):
        urgency = "High"
    elif any(w in lower for w in ["fever", "pain", "vomiting", "dizzy", "infection"]):
        urgency = "Medium"

    return {
        "urgency": urgency,
        "chief_complaint": symptoms_text[:120].strip() + ("..." if len(symptoms_text) > 120 else ""),
        "suggested_questions": [
            "How long have these symptoms been present?",
            "Have you taken any medications for relief?",
            "Are there any aggravating factors?"
        ]
    }


def _fallback_post_visit(clinical_notes, prescriptions=None):
    """Generates rule-based post-visit summary when offline/testing."""
    med_list = []
    if prescriptions:
        for item in prescriptions:
            med_list.append({
                "medication_name": item.get("medication_name", "Medication"),
                "schedule": f"{item.get('dosage', '1 tablet')} {item.get('frequency', 'daily')}",
                "advice": f"Take for {item.get('duration_days', 5)} days."
            })

    return {
        "patient_summary": f"Your doctor completed the visit: {clinical_notes[:150].strip()}",
        "medication_instructions": med_list,
        "follow_up": "Contact clinic if symptoms worsen or do not improve within 5 days."
    }
