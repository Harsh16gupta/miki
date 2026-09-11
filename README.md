Miki

Miki is an evidence-grounded interview trainer. It extracts claims from a resume and requirements from a job description, runs an interview session, and produces a scored report with cited evidence.

Stack

Backend: FastAPI, SQLAlchemy, Alembic, Postgres
Frontend: React, TypeScript, Vite
Voice: Deepgram STT and TTS, ElevenLabs TTS optional
Telemetry: Langfuse

Setup

Copy .env.example to .env and fill in the required keys.
Backend requires DATABASE_URL and JWT_SECRET_KEY. Voice requires DEEPGRAM_API_KEY. LLM calls require OPENROUTER_API_KEY.

Run backend

python -m venv venv
source venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn main:app --reload

Run frontend

cd frontend
npm install
npm run dev

The API runs on port 8000. The UI is served at /ui. API docs are at /docs.

Notes

See DESIGN.md for UI conventions.
See todo.md and implementation_plan.md for current development state.
