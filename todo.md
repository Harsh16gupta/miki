# Miki V1 — Build TODO (execute in order)

**How to use this file:** Each task is a single concrete step. Do not start a task until the previous one is checked off and actually working — not "probably working," verified. If you're using an AI assistant to help you code, paste one task at a time along with the relevant context section above it, not the whole file at once. Each phase ends with a "Checkpoint" — do not move to the next phase until the checkpoint passes.

---

## PHASE 0 — Environment & Repo Setup

- [x] Install Python 3.11+ and confirm with `python3 --version`.
- [x] Create the project repo (git init), with a `.gitignore` covering `__pycache__`, `.env`, `*.pyc`, `venv/`.
- [x] Create a virtual environment (`python3 -m venv venv`) and activate it.
- [x] Install FastAPI + Uvicorn (`pip install fastapi uvicorn[standard]`). Create a single `main.py` with one `GET /health` endpoint returning `{"status": "ok"}`. Run it, hit it with curl/browser, confirm it returns 200. **This is your "FastAPI works" sanity check — do not proceed until this returns successfully.**
- [x] Install and configure a Python linter/formatter (ruff or black + isort) and set up pre-commit or at least a habit of running it before commits.
- [x] Sign up for OpenRouter, get an API key, store it in a `.env` file (never commit this file).
- [x] Write a throwaway script `scratch/test_llm_call.py` that makes one raw HTTP call to OpenRouter's chat completions endpoint with a cheap model (e.g. DeepSeek) and prints the response. Confirm you get a real response back. **This is your "LLM access works" sanity check.**
- [x] Set up PostgreSQL locally (or a free-tier managed instance like Supabase/Neon) and confirm you can connect to it with `psql` or a GUI client.
- [x] Install SQLAlchemy + Alembic + psycopg (`pip install sqlalchemy alembic psycopg[binary]`). Initialize Alembic (`alembic init migrations`), point it at your database URL via `.env`.
- [x] Create one trivial table via a model + migration (e.g. a `ping` table with just an id) purely to confirm the SQLAlchemy → Alembic → Postgres pipeline works end to end. Run the migration, confirm the table exists in the database.

**Checkpoint 0 (PASSED):** You have a running FastAPI server, a working raw LLM call, and a working migration pipeline creating a real table in a real database. If any of these three don't work, do not proceed — fix them here.

---

## PHASE 1 — Core Data Model

Context: this schema is the backbone of the whole project. Getting the entities right now saves a rewrite in V2.

- [x] Design (on paper or in a doc, before code) the following tables and their key fields:
  - `candidate_profile`: id, raw_resume_text, extracted_json (JSON), created_at
  - `role_profile`: id, raw_jd_text, extracted_json (JSON), created_at
  - `session`: id, candidate_profile_id (FK), role_profile_id (FK), mode (string, e.g. "normal"), status (enum: in_progress/completed/aborted), started_at, ended_at, policy_version (string), engine_version (string)
  - `turn`: id, session_id (FK), turn_index (int), speaker (enum: candidate/miki), text, created_at
  - `claim`: id, session_id (FK), turn_id (FK, the turn it was extracted from), claim_text, category, confidence (float), created_at
  - `evidence`: id, claim_id (FK), turn_id (FK), evidence_text, evidence_type (enum: supports/contradicts/vague), created_at
  - `state_transition`: id, session_id (FK), from_state, to_state, proposed_by_llm (bool), was_validated (bool), rejection_reason (nullable string), model_id (string), created_at
  - `evaluation`: id, session_id (FK), dimension (string, e.g. "system_design"), score (float), evidence_refs (JSON array of evidence ids), rubric_version (string), model_id (string), created_at
- [x] Write SQLAlchemy models for each table above, with correct foreign keys and relationships.
- [x] Generate and run the Alembic migration for all of these tables.
- [x] Write a tiny script that manually inserts one fake row into each table (by hand, no LLM involved) and reads it back, to confirm the schema and relationships actually work before anything else depends on them.

**Checkpoint 1 (PASSED):** All tables exist in the database, relationships are enforced (test by trying to insert a `turn` with a non-existent `session_id` and confirming it fails), and you can manually write/read a full fake session's worth of data across all tables.

---

## PHASE 2 — LLM Wrapper + Telemetry

Context: every single LLM call in the whole project goes through this layer. Build it once, correctly, here.

- [x] Create `app/llm/router.py` with `call_llm(task_type: str, messages: list, response_format: dict | None) -> dict`.
- [x] Create `app/llm/model_config.yaml` mapping task types to model ids (static router). Cheap tasks → deepseek/deepseek-chat; question_generation/evaluation → anthropic/claude-sonnet-4.5.
- [x] Structured JSON output support in `call_llm` via `response_format` (verified live with deepseek, parses to `parsed_json`, raises loudly on invalid JSON).
- [x] Retry logic (2 retries on network/timeout/429/5xx with linear backoff, then raise; no retry on other 4xx).
- [x] Sign up for Langfuse (or self-host), get API keys → put `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` in `.env` (see `.env.example`).
- [x] Telemetry wrapper `app/telemetry/log_llm_call.py` (own thin function; rest of codebase never imports Langfuse). `call_llm` emits task_type, model_id, messages, output, latency_ms, success/failure + usage on every call. No-ops with a warning when keys are missing; never raises.
- [x] Test: trivial `call_llm` returns correctly AND call shows up in Langfuse dashboard (VERIFIED 2026-09-06: 2x `llm:extraction` traces in cloud project).

**Checkpoint 2 (CODE DONE, dashboard pending Langfuse keys):** One function + one config control all LLM calls; every call emits telemetry (currently warning-skipped until keys are set).

---

## PHASE 3 — Resume/JD Ingestion

- [x] Add file upload endpoint(s) (`POST /candidate-profile`, `POST /role-profile`) accepting PDF or plain text.
- [x] Add PDF text extraction (e.g. `pypdf` or `unstructured` library) for PDF uploads.
- [x] Write the extraction prompt for candidate profiles: input is raw resume text, output is structured JSON (skills list, projects list with descriptions, explicit claims list e.g. "reduced latency by 40%"). Use `call_llm` with `task_type="extraction"` and JSON response format.
- [x] Write the equivalent extraction prompt for role profiles (required skills, preferred skills, responsibilities, seniority signal).
- [x] Wire both endpoints to: save raw text → call extraction → save extracted JSON to the `candidate_profile` / `role_profile` tables.
- [ ] Test with your actual resume and a real job description you're targeting. Manually inspect the extracted JSON for accuracy — fix the prompt if it's missing obvious claims or projects.

**Checkpoint 3:** You can upload your real resume and a real JD and get back sensible structured JSON, stored in the database, traceable in Langfuse.

---

## PHASE 4 — Interview Policy Config

- [x] Write `policies/normal_interview.yaml` (or JSON) by hand, containing at minimum:
  - `target_duration_minutes`: e.g. 40
  - `min_projects_covered`: e.g. 2
  - `min_required_skills_covered`: e.g. 3
  - `max_followups_per_claim`: e.g. 3
  - `difficulty_escalation_rule`: plain description (e.g. "escalate after 2 consecutive strong answers in the same category")
  - `difficulty_deescalation_rule`: plain description
  - `silence_threshold_seconds`: 3–5 (used later by the voice layer, defined here since it's policy, not audio-code detail)
  - `closing_rule`: plain description (e.g. "close once min coverage is met AND duration >= target_duration_minutes, or hard-cap at target_duration_minutes + 15")
- [x] Write a small Python loader that parses this file into a typed config object (e.g. a Pydantic model) so the rest of the code references typed fields, not raw dict lookups.
- [x] Add a `policy_version` field/string (can just be a semantic version you bump manually, e.g. "0.1") that gets stamped onto every `session` row using this policy.

**Checkpoint 4:** You have one file that fully defines interview behavior, loaded into a typed object, versioned.

---

## PHASE 5 — State Machine Skeleton (no LLM yet)

Context: prove the skeleton and persistence work with zero AI involved before adding any intelligence.

- [x] Define the state enum in code: `OPENING, PROBING_CLAIM, FOLLOWING_UP, ESCALATING, DE_ESCALATING, REDIRECTING, CLOSING`.
- [x] Define the legal-transition table in code as an explicit structure (e.g. a dict mapping each state to the set of states it's allowed to transition to). Example: `OPENING` can only go to `PROBING_CLAIM`; `CLOSING` can't transition anywhere.
- [x] Write a `StateMachine` class with: current_state, a `propose_transition(target_state, reason)` method that checks the proposal against the legal-transition table and the policy config, and either accepts (persists a `state_transition` row with `was_validated=True`) or rejects (persists with `was_validated=False` and a `rejection_reason`).
- [x] Write a manual test script that hardcodes a fixed sequence of transitions (no LLM) — some legal, some deliberately illegal — and confirms the validator accepts the legal ones and rejects the illegal ones, with rows correctly written to `state_transition`.

**Checkpoint 5:** The state machine correctly enforces the legal-transition table and policy rules against hardcoded input, with zero LLM involvement, and every transition (accepted or rejected) is persisted and traceable.

---

## PHASE 6 — Claim/Evidence Extraction (real LLM call)

- [x] Write the extraction prompt: input is the candidate's latest answer (plus recent conversation context), output is structured JSON listing: claims made, a category per claim, a confidence/vagueness signal, and whether it contradicts an earlier claim or the resume.
- [x] Wire this as `call_llm(task_type="extraction", ...)`.
- [x] On receiving output, write rows to `claim` and `evidence` tables, linked to the correct `turn`.
- [x] Test against 3–5 hand-written fake candidate answers (not live yet) covering: a strong specific answer, a vague answer, an answer contradicting an earlier one. Manually verify the extracted claims/evidence look right for each.

**Checkpoint 6:** Given any candidate answer (fake, typed), you get back correctly structured claims and evidence, persisted and linked to the right turn.

---

## PHASE 7 — Transition Proposal (real LLM call) + Validation Integration

- [x] Write the state-transition-proposal prompt: input is current state, policy config, recent claims/evidence, coverage-so-far; output is structured JSON `{proposed_state, target_claim_id, reason}`.
- [x] Wire as `call_llm(task_type="state_transition_proposal", ...)`.
- [x] Feed the LLM's proposal into the `StateMachine.propose_transition()` method built in Phase 5 — do NOT let the LLM's proposal be applied directly; it must go through the validator.
- [x] Test: manually construct a scenario likely to produce an illegal proposal (e.g. prompt state such that the model might propose closing too early) and confirm the validator correctly rejects it and the session continues in a sane state rather than crashing.

**Checkpoint 7:** The LLM proposes transitions, but only validator-approved transitions are ever actually applied — and you have a concrete example of an illegal proposal being caught.

---

## PHASE 8 — Question/Probe Generation (real LLM call)

- [x] Write the question-generation prompt: input is the validated current state, policy, target claim (if probing), candidate/role profile; output is the actual next question text (not structured JSON this time — this is user-facing text).
- [x] Wire as `call_llm(task_type="question_generation", ...)`.
- [x] Persist the generated question as a `turn` row (speaker = miki).

**Checkpoint 8:** Given a validated state, you get a real, coherent interview question as output.

---

## PHASE 9 — Text-Only Interview Loop (full end-to-end, no voice)

- [x] Build a simple CLI or minimal text-based endpoint (`POST /session/{id}/answer`) where you type a candidate answer, and the system runs: extraction (Phase 6) → transition proposal + validation (Phase 7) → question generation (Phase 8) → returns the next question, looping until the state machine reaches `CLOSING`.
- [x] Add session start/end endpoints: `POST /session/start` (given candidate_profile_id + role_profile_id + mode) initializes state to `OPENING` and generates the first question; the loop above continues until closing.
- [ ] **Run a full interview on yourself by typing answers, start to finish**, using your real resume/JD. Do not skip this — this is the most important test in the entire V1 build.
- [ ] Fix whatever breaks. Expect this step to reveal several prompt/logic issues — that's normal and expected, this is why it's a dedicated phase before voice.

**Checkpoint 9 (major milestone):** You can run a complete, coherent, policy-compliant interview by typing, from start to natural close, on your real resume/JD.

---

## PHASE 10 — Synthetic State-Machine Test Cases

- [x] Write 5–8 scripted "fake candidate" answer sequences designed to specifically trigger: a probe-worthy claim, a weak/vague answer, a strong answer that should escalate difficulty, two weak answers in a row that should NOT over-escalate, an answer contradicting an earlier one.
- [x] Run each scripted sequence through the Phase 9 loop (feeding the fake answers programmatically instead of typing) and manually verify the resulting state transitions match what the policy *should* produce.
- [x] Where they don't match, fix the transition-proposal prompt or the policy config (not just a one-off code patch) — the goal is to make correct behavior emerge from the config/prompt design, not a special case.

**Checkpoint 10:** You have a repeatable regression test you can rerun any time you touch the state machine, transition prompt, or policy config.

---

## PHASE 11 — Rubric + Evaluator

- [x] Write `rubrics/normal_interview.yaml` by hand: list of evaluation dimensions (e.g. technical_correctness, depth, trade_off_reasoning, communication, claim_defensibility), and for each, a description of what a low/medium/high score actually looks like in evidence terms.
- [x] Add a `rubric_version` field, versioned like the policy config.
- [x] Write the evaluation prompt: input is the rubric, the full transcript, and all extracted claims/evidence for the session; output is structured JSON with a score per dimension AND a list of evidence references (pointing at specific claim/evidence/turn ids) justifying each score.
- [x] Wire as `call_llm(task_type="evaluation", ...)`, triggered when a session reaches `CLOSING`.
- [x] Persist results to the `evaluation` table, with `evidence_refs` populated.

**Checkpoint 11:** Ending a session automatically produces a structured, evidence-cited evaluation, stored and traceable.

---

## PHASE 12 — Evaluation Calibration

- [ ] Run (or reuse) 10–15 full text-based interview sessions from Phase 9/10 testing.
- [ ] For each, manually score it yourself against the rubric, independently, before looking at Miki's evaluator output.
- [ ] Compare your manual scores to the evaluator's scores per dimension. Note where they diverge significantly.
- [ ] Adjust the rubric wording and/or evaluation prompt to close the biggest gaps. Re-run the comparison until agreement is reasonably close (you decide the bar — it doesn't need to be perfect, it needs to be "trustworthy enough that a big divergence would surprise you").
- [ ] Keep this set of 10–15 hand-scored transcripts in the repo — this becomes the seed for V3's meta-evaluation harness.

**Checkpoint 12:** You have documented evidence that the evaluator's scores are reasonably aligned with your own judgment, on a fixed set of examples you can rerun later.

---

## PHASE 13 — Post-Interview Report

- [ ] Build a simple rendering (JSON API response is fine for V1, pretty HTML/UI optional) showing: per-dimension scores with cited evidence, a plain-language summary of strengths/weaknesses, which resume claims were hard to defend, and suggested study topics (can be a simple LLM call over the evaluation output, or written logic — your call).

**Checkpoint 13:** After a session ends, you get a report you'd actually want to read.

---

## PHASE 14 — Voice Adapter Layer

Context: the interview engine (Phases 5–9) has a strict text-in/text-out contract. Nothing in this phase touches engine code — you are only building the audio wrapper around it.

- [ ] Sign up for your chosen STT provider, get API access, confirm streaming support.
- [ ] Sign up for your chosen TTS provider, get API access.
- [ ] First test STT and TTS completely standalone, with pre-recorded audio files (not live mic, not WebSocket yet) — confirm you can send an audio file and get correct transcribed text back, and send text and get correct synthesized audio back.
- [ ] Build the WebSocket endpoint (`/session/{id}/voice`) that: receives streamed audio chunks from the client, feeds them to STT, accumulates transcribed text.
- [ ] Implement silence-based turn detection: using the `silence_threshold_seconds` from the policy config, detect when the candidate has stopped talking (via STT's voice activity detection or a timing-based heuristic) and only then treat the accumulated transcript as a complete "turn," feeding it into the same `POST /session/{id}/answer` logic built in Phase 9.
- [ ] On receiving the next question text from the engine, call TTS and stream the resulting audio back to the client over the WebSocket.
- [ ] Test with a simple browser client or minimal script capturing real mic input, round-tripping through the whole pipeline.

**Checkpoint 14:** You can speak an answer, have it transcribed, processed by the unchanged text-engine, and hear Miki's spoken response back — with the engine code itself untouched from Phase 9–13.

---

## PHASE 15 — Full End-to-End Voice Interview

- [ ] Run one complete real voice interview on yourself, start to finish, using your actual resume and a real job description, entirely by talking.
- [ ] Review the resulting transcript, state-transition trace (via Langfuse + the `state_transition` table), and evaluation report together. Confirm they're coherent and match your memory of how the interview actually went.
- [ ] Fix whatever's broken. This is your V1 completion milestone.

**Checkpoint 15 (V1 DONE):** A real 30–45+ minute voice interview, run against your real resume/JD, produces a coherent, policy-compliant session and a trustworthy, evidence-cited evaluation report — and you can explain, from logged data, why Miki asked what it asked at any point in the interview.

---

## After V1

Do not start V2 (persistent memory, additional modes, company intel) until Checkpoint 15 has actually passed on a real, unscripted voice interview — not a scripted test case. V2's memory model depends on V1's `claim`/`evidence` schema being solid; if you find yourself wanting to change that schema significantly while building V2, that's a sign to pause and reconsider rather than bolt memory logic onto a shaky foundation.