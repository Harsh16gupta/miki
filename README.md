# Miki — Evidence-Grounded Interview Trainer

Miki turns interview prep into deliberate practice. Upload a resume and a job description, run a structured mock interview with text or voice, and get a scored report where every judgment links back to what you actually said.

Instead of generic feedback like "improve your depth," Miki cites the specific claims you made, the evidence you gave (or didn't), and where your answers held up or fell apart.

## Why Miki

Most mock interview tools generate questions and give vague scores. Miki is built around three principles:

1. **Claims first.** Your resume is parsed into verifiable claims. The interviewer probes those claims, not random questions.
2. **Evidence attached.** Every score references turn IDs, claim IDs, and evidence IDs — you can trace any judgment back to the transcript.
3. **Policy over prompting.** Interview behavior (follow-up limits, escalation, closing rules) is enforced in code with an audited state machine, not left to LLM whims.

## Product Flow

**1. Setup** — Upload a resume (PDF/txt) and a job description. Miki extracts candidate claims, skills, projects, and role requirements.

**2. Interview** — Answer questions via text or voice. Miki tracks claims in real time, follows up within policy limits, escalates when you're strong, and scaffolds when you're stuck.

**3. Report** — When the session completes, you get dimension scores (1–5), an overall score, strengths, areas for improvement, vulnerable claims, and study topics — all with citations.

## Features

- Resume/JD ingestion with structured extraction (skills, projects, claims, seniority signals)
- Stateful interview engine with validated transitions (`OPENING → PROBING → FOLLOWING_UP → ESCALATING / DE-ESCALATING → CLOSING`)
- Per-answer claim + evidence extraction (supports / contradicts / vague)
- Versioned rubric evaluation: technical correctness, depth, trade-off reasoning, communication, claim defensibility
- Voice interviews over WebSocket (Deepgram STT/TTS, optional ElevenLabs TTS)
- Auth with guest + registered sessions, session history, abort/resume handling
- LLM telemetry via Langfuse

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2, Alembic, Postgres
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, React Router 7
- **LLM:** Meta Model API (`muse-spark-1.3-contributor`) with OpenRouter fallback — per-task model routing in `app/llm/model_config.yaml`
- **Voice:** Deepgram Nova-2 STT + Aura TTS, ElevenLabs optional
- **Telemetry:** Langfuse

## Getting Started

### Prerequisites

- Python 3.11+, Node 18+, Postgres 14+
- An LLM API key. Voice requires a Deepgram key.

### 1. Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env   # fill in keys, see Configuration
alembic upgrade head
uvicorn main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the app:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Production UI build: `http://localhost:8000/ui`
- Dev UI: `http://localhost:5173`

To serve the frontend from FastAPI in production:

```bash
npm run build:ui
```

## Configuration

All config lives in `.env` (see `.env.example`).

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string |
| `JWT_SECRET_KEY` | Yes | Signs auth tokens |
| `META_API_KEY` | Yes (default) | LLM calls via Meta Model API |
| `OPENROUTER_API_KEY` | If `LLM_PROVIDER=openrouter` | Fallback LLM provider |
| `DEEPGRAM_API_KEY` | For voice | STT + default TTS |
| `TTS_PROVIDER` | No | `deepgram` (default) or `elevenlabs` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | No | LLM call tracing |

## Architecture

```text
Resume/JD
  -> ingest + extraction (candidate_profile, role_profile)
  -> session loop: question -> answer -> claims -> propose state -> validate -> next question
  -> completion -> rubric evaluation -> report with citations
```

Key directories:

```text
main.py               FastAPI app, router mounting, /ui static mount
app/routers/          auth, profiles, sessions, voice
app/interview/        state machine, policy gates, question generation, loop
app/extraction/       per-answer claim/evidence extraction
app/evaluation/       rubric loading, scoring, report building
app/llm/              single LLM gateway + task-to-model routing
app/voice/            STT/TTS providers, turn-end detection
app/models/           SQLAlchemy models (profiles, sessions, turns, claims, evidence, evaluations)
policies/             interview policy YAML (durations, coverage, follow-up caps)
rubrics/              evaluation rubric YAML (dimensions, scale)
frontend/src/         pages: Setup, Interview, Report + history/auth
```

Interview policy and rubric are versioned and stamped onto each session, so reports stay reproducible as prompts and models change.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/candidate-profile` `/candidate-profile/upload` | Create candidate profile |
| POST | `/role-profile` `/role-profile/upload` | Create role profile |
| POST | `/session/start` | Start interview |
| POST | `/session/{id}/answer` | Submit answer, get next question |
| GET | `/session/{id}` | Session state + transcript |
| GET | `/session/{id}/report` | Scored report (completed sessions) |
| POST | `/session/{id}/abort` | Abort session |
| GET | `/sessions/history` | Own history (authenticated) |
| WS | `/session/{id}/voice?token=` | Voice channel |

Full schema is available at `/docs` when the backend is running.

## Development Notes

- Design system: see `DESIGN.md` (tokens, stage-driven layout, component rules).
- Frontend specs: `docs/frontend-rebuild/`.
- Calibration vignettes for the evaluator live in `calibration/`.

## License

MIT — see `LICENSE`.

This repo is still under development.
