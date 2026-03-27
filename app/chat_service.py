import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# Default to a known-available model; can be overridden by GEMINI_MODEL
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def _extract_text(resp):
    if resp is None:
        return None
    # Try common attributes
    for attr in ("text", "output", "result", "content"):
        if hasattr(resp, attr):
            val = getattr(resp, attr)
            if isinstance(val, str):
                return val
            # list-like handling
            try:
                if isinstance(val, (list, tuple)) and len(val) > 0:
                    first = val[0]
                    if isinstance(first, str):
                        return first
                    if hasattr(first, "text"):
                        return getattr(first, "text")
                    if hasattr(first, "content"):
                        return getattr(first, "content")
            except Exception:
                pass
    # candidates pattern
    try:
        cands = getattr(resp, "candidates", None)
        if cands:
            first = cands[0]
            if hasattr(first, "output"):
                return getattr(first, "output")
            if hasattr(first, "content"):
                return getattr(first, "content")
    except Exception:
        pass
    # Fallback to string
    try:
        return str(resp)
    except Exception:
        return None


def generate_chat_response(message, user_data, chat_history, summary):
    try:
        prompt = f"""
You are a caring mental health companion.

Previous summary:
{summary}

- Talk like a close friend
You are a caring and emotionally intelligent friend. You are NOT a doctor.

Rules:
- Be warm, casual, and human; speak like a supportive best friend.
- Keep responses 3–5 lines.
- Follow this structure in order: Empathy, Insight, Suggestion, Question.
- Mirror feelings, validate the user, and detect emotion.
- Offer one small actionable micro-strategy (breathing, short break, hydrate, grounding).
- Use light emoji use and occasional gentle humor for MEDIUM stress.
- Vary sentence openings and question types across replies.

Escalation guidance:
- If risk level is "LOW": normal friendly chat.
- If "MEDIUM": offer comforting advice and 1 quick strategy.
- If "HIGH": adopt a serious, supportive tone and suggest immediate coping steps.
- If "CRITICAL": encourage contacting a trusted person or professional and provide crisis resources.

Memory: previous summary (for context):
{summary}

User profile:
Stress score: {user_data.get('stress_score')}
Risk level: {user_data.get('risk_level')}
Sleep hours: {user_data.get('sleepHours')}
Screen time: {user_data.get('screenTime')}
Step count: {user_data.get('stepCount')}
AQI: {user_data.get('aqi')}
Mood: {user_data.get('mood')}

Conversation so far:
{chat_history}

User: {message}

Instructions to assistant:
- Start by naming or reflecting the emotion (e.g., "That sounds really overwhelming…").
- Then give a brief insight (1 sentence) about what might be contributing.
- Offer exactly ONE actionable micro-strategy (breathing, 1-min stretch, hydrate, ground).
- End with one open follow-up question.
- If stress is MEDIUM, you may add a light humorous line (e.g., "Looks like your brain opened 47 tabs today 😅").
- If HIGH or CRITICAL, be more serious; avoid jokes.
- Keep language simple and human; avoid clinical jargon.
- Use an emoji once or twice max.

Respond now following the rules above.
"""
        response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt
)

        print("🔥 RAW RESPONSE:", response)

        # ✅ SAFE EXTRACTION
        if hasattr(response, "text") and response.text:
            return response.text

        if response.candidates:
            return response.candidates[0].content.parts[0].text

        return "I'm here for you. Tell me what's on your mind."

    except Exception as e:
        import traceback
        print("❌ GEMINI ERROR:")
        traceback.print_exc()

        return f"ERROR: {str(e)}"


def update_stress(message, current_stress):
    text = message.lower()

    if any(w in text for w in ["stressed", "angry", "tired", "overwhelmed"]):
        current_stress += 1
    elif any(w in text for w in ["better", "relaxed", "good", "fine"]):
        current_stress -= 1

    return max(1, min(10, current_stress))

  
def generate_summary(chat_history):
    prompt = f"""
Summarize this conversation for mental health tracking.

Conversation:
{chat_history}

Include:
- main issue
- emotional state
- improvement

Keep it short (2-3 lines).
"""
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        print("GENAI_RAW_SUMMARY_RESPONSE:", response)
        if hasattr(response, "text") and response.text:
            return response.text
        if getattr(response, "candidates", None):
            return response.candidates[0].content.parts[0].text
    except Exception:
        traceback.print_exc()

    return "(summary unavailable — model service error)"
