from fastapi import FastAPI
from app.schemas import ChatMessageInput, StartChatInput, EndChatInput
from app.chat_service import (
    generate_chat_response,
    update_stress,
    generate_summary
)
from app.utils import classify_risk
import os
from dotenv import load_dotenv

load_dotenv()

# Ensure user site-packages is on sys.path (useful when packages were installed with --user)
try:
    import site, sys
    usersite = site.getusersitepackages()
    if usersite not in sys.path:
        sys.path.insert(0, usersite)
except Exception:
    pass

# Safely import and initialize the new genai client. If unavailable, keep `client` None
client = None
try:
    import google.genai as genai
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        # Print the exception so server logs show why client creation failed
        import traceback
        print("genai.Client init exception:", repr(e))
        traceback.print_exc()
        client = None
except Exception:
    genai = None
    client = None


app = FastAPI(title="AI Chat Service")


@app.get("/models")
def list_models():
    # Try to construct a client at call-time so we can return detailed errors
    try:
        import google.genai as genai_local
    except Exception as e:
        return {"error": f"import google.genai failed: {e!r}"}

    try:
        client_local = genai_local.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        return {"error": f"genai.Client init failed: {e!r}"}

    try:
        model_names = []
        if hasattr(client_local, "models") and hasattr(client_local.models, "list"):
            resp = client_local.models.list()
            for m in getattr(resp, "models", resp) or []:
                model_names.append(getattr(m, "name", str(m)))
            return {"models": model_names}

        if hasattr(client_local, "list_models"):
            resp = client_local.list_models()
            for m in resp or []:
                model_names.append(getattr(m, "name", str(m)))
            return {"models": model_names}

        return {"error": "list models API not found on client"}
    except Exception as e:
        return {"error": str(e)}
@app.get("/")
def home():
    return {"message": "Chat API running"}


# 💬 CHAT
@app.post("/chat")
def chat(input: ChatMessageInput):

    # Chat (ongoing message) - uses provided fields but no external summary
    reply = generate_chat_response(
        input.message,
        input.dict(),
        input.chat_history,
        ""  # no summary during in-chat messages
    )

    new_stress = update_stress(input.message, input.stress_score)
    risk = classify_risk(new_stress)

    return {
        "reply": reply,
        "updated_stress_score": new_stress,
        "updated_risk_level": risk
    }


# START CHAT (new)
@app.post("/startchat")
def start_chat(input: StartChatInput):

    # Initial conversation start; client may include a summary for memory-based replies
    reply = generate_chat_response(
        input.message,
        input.dict(),
        input.chat_history,
        input.summary
    )

    new_stress = update_stress(input.message, input.stress_score)
    risk = classify_risk(new_stress)

    return {
        "reply": reply,
        "updated_stress_score": new_stress,
        "updated_risk_level": risk
    }


# 🧾 END CHAT
@app.post("/end-chat")
def end_chat(input: EndChatInput):

    summary = generate_summary(input.chat_history)

    return {
        "final_stress_score": input.stress_score,
        "final_risk_level": input.risk_level,
        "summary": summary
    }
