# Miki

Miki is an evidence-grounded interview trainer. Upload a resume and a job description, run a mock interview with text or voice, and get a scored report with citations to what you actually said.

## Features

- Resume and job description ingestion (PDF or text)
- Structured interviews driven by a policy-based state machine
- Claim and evidence extraction from every answer
- Rubric-based scoring with traceable citations
- Voice interviews over WebSocket
- Auth, session history, and reports

## Stack

FastAPI, SQLAlchemy, Alembic, Postgres · React, TypeScript, Vite, Tailwind CSS · Deepgram voice · Langfuse telemetry

## Getting Started

Requirements: Python 3.11+, Node 18+, Postgres 14+.

Backend:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- UI: `http://localhost:8000/ui` (or `http://localhost:5173` in dev)

## Configuration

See `.env.example`. Required: `DATABASE_URL`, `JWT_SECRET_KEY`, `META_API_KEY`. Optional: `DEEPGRAM_API_KEY` (voice), Langfuse keys (telemetry).

## Structure

```text
main.py            FastAPI entrypoint
app/               routers, interview engine, evaluation, LLM, voice, models
policies/          interview policy
rubrics/           evaluation rubric
frontend/src/      Setup, Interview, Report pages
migrations/        Alembic migrations
```

## License

MIT — see `LICENSE`.

This repo is still under development.
