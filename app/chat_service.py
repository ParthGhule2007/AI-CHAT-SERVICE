import os
import traceback
import random
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
        # Determine risk level and pick a response mode
        risk = (user_data.get("risk_level") or "LOW").upper()
        from app.utils import choose_response_mode, CALMING_MICRO

        mode = choose_response_mode(risk)

        # Detect drained / exhaustion signals from message or user context
        text_lower = (message or "").lower()
        drained_keywords = ["exhaust", "drain", "burnout", "mentally drained", "completely exhausted", "wiped", "too tired", "tapped out"]
        is_drained = any(k in text_lower for k in drained_keywords)

        # Use context smartly (sleepHours, screenTime, stepCount) to bias handling
        try:
            sleep_h = float(user_data.get("sleepHours") or 0)
        except Exception:
            sleep_h = 0
        try:
            screen_t = float(user_data.get("screenTime") or 0)
        except Exception:
            screen_t = 0
        try:
            steps = int(user_data.get("stepCount") or 0)
        except Exception:
            steps = 0

        # If user shows drained signals or very low sleep and risk is HIGH/CRITICAL,
        # force calmer deep-support / listen behaviour.
        if risk in ("HIGH", "CRITICAL") and (is_drained or sleep_h and sleep_h < 4 or screen_t and screen_t > 8 or steps and steps < 1000):
            mode = "deep_support"

        # Build a concise instruction set that emphasizes variability and short replies
        prompt = f"""
You are a caring friend-style mental health companion. Keep replies short (2-4 lines),
casual, and human. Use small pauses '...' and one light emoji max unless CRITICAL.

Mode: {mode}

Context (use naturally, don't list data):
Summary: {summary}
Recent chat: {chat_history}
User: {message}

Risk: {risk}

Rules by mode:
- empathy_only: respond with a warm, validating 1-2 line empathy statement. No advice.
- empathy_question: empathize briefly, then ask one gentle open question.
- empathy_suggestion: empathize, offer one tiny micro-action (like a breathing cue), then a short follow-up.
- empathy_humor: light empathy + a tiny, kind joke or metaphor (only for LOW/MEDIUM).
- deep_support: longer empathy (still keep 2-4 short lines), calm tone, minimal advice, encourage support.
- listen: mirror feelings and invite them to continue; do NOT give advice.

Also:
- If risk is HIGH or CRITICAL, prefer 'listen' or 'deep_support' and avoid jokes.
- Use grounding/micro-techniques when offering suggestions. Possible options: {CALMING_MICRO}
- Keep language simple, natural, friend-like (hey, hmm, yeah...), avoid clinical/jargon tone.

SPECIAL HANDLING RULES:

If stress_level is HIGH or CRITICAL:
- Do NOT jump into questions immediately.
- First calm the user emotionally with slow, supportive language and grounding cues.
- Acknowledge exhaustion deeply when user indicates being drained or very low sleep.
- Avoid overwhelming advice; focus on rest and reassurance.
- Only ask a question AFTER a clear calming/supportive message.

If the user expresses exhaustion or burnout:
- Use phrases like: "let's slow this down", "take a breath with me", "you're not alone in this".
- Connect gently to context (e.g., lack of sleep) without listing numbers: "Not getting enough rest can really drain you."

Respond now following the single selected Mode and rules above.

Respond now following the single selected Mode and rules above.
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        print("🔥 RAW RESPONSE:", response)

        # Extract text safely
        text = None
        if hasattr(response, "text") and response.text:
            text = response.text
        else:
            cands = getattr(response, "candidates", None)
            if cands:
                try:
                    text = cands[0].content.parts[0].text
                except Exception:
                    try:
                        text = str(cands[0])
                    except Exception:
                        text = None

        if not text:
            return "Hey... I'm here for you. Want to tell me more?"

        # Post-process: ensure 2-4 short lines, keep ellipses and casual words
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) == 0:
            return "Hey... I'm here with you."

        # Truncate to maximum 4 lines, but keep sentences intact
        out_lines = lines[:4]
        # Ensure brevity: if any line is very long, wrap/truncate to shorter sentence fragments
        trimmed = []
        for ln in out_lines:
            if len(ln) > 160:
                trimmed.append(ln[:157].rstrip() + "...")
            else:
                trimmed.append(ln)

        final = "\n".join(trimmed)

        # Extra safety for HIGH/CRITICAL: ensure we don't immediately ask questions
        if risk in ("HIGH", "CRITICAL"):
            # If final ends with a question or contains a leading question line, remove it
            lines_lower = [ln for ln in trimmed]
            # If the last line is a question, drop it
            if lines_lower and lines_lower[-1].strip().endswith("?"):
                lines_lower = lines_lower[:-1]
            # Also prevent directive advice in deep_support mode; keep calm lines
            final_candidate = "\n".join(lines_lower).strip()
            # If result is empty or still looks like advice, fallback to a calming template
            if not final_candidate or any(w in final_candidate.lower() for w in ["you should", "try this", "schedule", "improve"]):
                # Natural, human calming fallback
                extra = []
                extra.append("Hey... that sounds really overwhelming 💙")
                if is_drained or (sleep_h and sleep_h < 4):
                    extra.append("Seems like you're running on very little rest — that can really drain you.")
                extra.append("Let's slow it down for a moment — take a deep breath in... and out...")
                extra.append("I'm here with you. You don't have to carry this alone.")
                return "\n".join(extra)
            return final_candidate

        # Extra safety: if mode==listen, strip advice-like directives (best-effort)
        if mode == "listen":
            if any(w in final.lower() for w in ["should", "you should", "try", "maybe try", "sleep"]):
                return "That sounds really heavy... I'm here with you. Want to tell me more?"

        return final

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
