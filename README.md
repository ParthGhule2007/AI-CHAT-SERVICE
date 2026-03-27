# AI Chat Service

Simple FastAPI-based mental health chat service using Gemini (Google Generative AI).

Prerequisites
- Python 3.10+
- A Gemini API key

Install

```bash
pip install -r requirements.txt
```

Set API key in `.env`:

```
GEMINI_API_KEY=your_api_key_here
```

Run locally

```bash
uvicorn app.main:app --reload
```

Open the interactive docs:

http://127.0.0.1:8000/docs

Notes
- Update the `GEMINI_API_KEY` in `.env` before testing endpoints that call the model.
- Files are in the `app/` package: `main.py`, `chat_service.py`, `schemas.py`, `utils.py`.
