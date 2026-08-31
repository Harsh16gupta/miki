# Miki — Full Implementation Plan (V1 / V2 / V3)

## What Miki is, in one paragraph

Miki is a voice-first, personalized AI interview training system for Software Engineer / AI Engineer candidates. A candidate uploads a resume and a job description; Miki conducts a realistic 30–60 minute voice interview that adapts in real time — probing resume claims, following up on weak answers, escalating or de-escalating difficulty based on demonstrated ability. After the interview, Miki produces an evidence-grounded evaluation report, not an arbitrary score. Over time (V2+), Miki remembers what a candidate is good and bad at across sessions, so later interviews are smarter than earlier ones. Eventually (V3) it closes the loop by turning detected weaknesses into targeted practice drills.

The system is built primarily from first principles — no agent frameworks (LangChain/LangGraph) driving the core logic — because the point of the project is to demonstrate real AI/systems engineering, not to wire together existing frameworks.

---

## Locked technology decisions (apply across all versions unless noted)

| Decision | Choice | Notes |
|---|---|---|
| Backend language/framework | Python 3.11+, FastAPI | chosen over Node/TS for AI-engineering job-market alignment; short deliberate ramp-up before V1 build starts |
| LLM access | OpenRouter, thin static task→model config wrapper | no intelligent/adaptive routing in V1; you manually assign a model per task type |
| Default/cheap models | e.g. DeepSeek V3, GLM-4.6 (whatever is cheapest/best at time of building) | used for high-volume, lower-stakes calls (extraction, memory writes) and all dev/debug iteration |
| Interview-facing model | a stronger reasoning model (e.g. Claude, GPT-tier) | used for question generation and final evaluation, where quality matters most |
| Database | PostgreSQL | single database for all structured data |
| Vector capability | pgvector extension (added in V2) | avoids a second database system |
| ORM / migrations | SQLAlchemy + Alembic | migrations discipline from the first schema |
| Observability | Structured telemetry emitted by Miki's own code, piped to Langfuse as a sink | core code never imports/depends on Langfuse directly — telemetry emission is yours, Langfuse just consumes it |
| Orchestration frameworks | None (no LangChain, no LangGraph) in V1 | state machine and call chains built and owned by you; frameworks can be reconsidered only after you've built your own and understand what they'd replace |
| STT | A streaming-capable provider (e.g. Deepgram, AssemblyAI) | evaluated on latency + cost, not just accuracy |
| TTS | A reasonably fast, reasonably cheap provider (e.g. ElevenLabs, Cartesia, or OpenAI TTS) | same criteria |
| Transport | WebSocket (FastAPI native) | needed for streaming audio regardless of framework |
| Frontend | Minimal — plain React or lightweight server-rendered UI | not where the project's learning value is; keep it thin throughout |

## Standing architectural principle (applies at every version)

**The LLM is responsible for interpretation, extraction, reasoning proposals, and generation. Application code is responsible for state, validation, business rules, persistence, orchestration, and safety constraints.** Concretely: an LLM call can *propose* a state transition, an evaluation score, or a memory write — but a piece of deterministic code checks that proposal against explicit rules before it's accepted and persisted. Whenever you catch yourself about to let an LLM call directly decide something structural (what state to move to, whether a transition is legal, how a score should be weighted), stop and write that rule in code instead.

---

# V1 — "Interview Me"

### Goal
Give Miki a resume and a job description, have a real 30–60 minute **voice** interview that adapts to your answers, and receive a report you'd trust more than your own self-assessment of how the interview went.

### Scope boundary — V1 explicitly does NOT include
- Cross-session / persistent memory of any kind (every interview starts from zero knowledge of you beyond the resume/JD given at session start)
- Company research or web scraping
- GitHub/project analysis
- More than one interview mode ("normal interview" only)
- Barge-in / interruption handling (silence-based turn-taking only)
- An intelligent/adaptive model router (static per-task config only)
- Any agent framework (LangChain/LangGraph)
- A polished frontend
- Redis or any infrastructure beyond Postgres
- An automated meta-evaluation/drift-tracking system (a one-time manual calibration check is enough for V1)

### V1 components, explained

**1. Candidate & role profiles.** Resume and job description are uploaded, text is extracted (PDF/text parsing), and a single LLM call structures each into a JSON profile: for the candidate, a list of skills, projects, and specific claims (e.g. "reduced latency by 40%"); for the role, required skills, responsibilities, and seniority signals. These profiles stay as JSON — they're the one place in the schema where an unstructured blob is the right call, because they're consumed as context, not queried or reasoned over structurally.

**2. Interview policy.** A single YAML/JSON config file (checked into version control) defining, for the "normal interview" mode: target duration, what "coverage" means (e.g. must touch at least N of the candidate's listed projects and M of the role's required skills), follow-up depth rules (how many follow-ups on a single claim before moving on), difficulty escalation/de-escalation rules, the silence-duration threshold that signals the candidate has finished speaking (3–5 seconds to start), and closing rules (when/how the interview wraps up). This file is the single source of truth for "how should this interview behave" — nothing about pacing, coverage, or closing logic should live inside a prompt instead of here.

**3. State machine (application-owned).** An explicit set of states (e.g. `opening`, `probing_claim`, `following_up`, `escalating`, `de_escalating`, `redirecting`, `closing`) and a table of legal transitions between them, defined in code. At each turn: an LLM call proposes a transition (structured JSON output: `{proposed_state, target_claim_id, reason}`), and a deterministic validator function checks the proposal against the legal-transition table and the interview policy config (e.g. rejects "escalate" if the policy says minimum coverage hasn't been met yet, or corrects "close" if under minimum duration). Only validated transitions are persisted and acted on. This is the component most responsible for Miki actually being an engineered system rather than a scripted persona.

**4. Claim/evidence extraction.** After every candidate answer, a dedicated LLM call (separate from question generation) extracts: claims made in the answer, confidence/vagueness signals, and any contradictions with earlier answers or the resume. Output is structured and written to first-class `claim` and `evidence` database rows — not appended to a growing text blob. This extraction is what the state machine's transition proposals and the final evaluator both depend on, so its quality bounds the quality of everything downstream.

**5. Question/probe generation.** A separate LLM call that, given the current (validated) state, the interview policy, and relevant claims/evidence, generates the actual next question or follow-up shown/spoken to the candidate.

**6. Evaluation pipeline.** A rubric is written by hand (not generated by an LLM) as a versioned config: evaluation dimensions (technical correctness, depth, trade-off reasoning, communication, etc.), what evidence looks like at each score band. At the end of a session, one LLM call takes the rubric + full transcript + extracted claims/evidence and produces scores where every score must cite specific evidence (a transcript moment or claim), not just a justification sentence.

**7. Evaluation calibration (small, V1-scoped).** Before trusting the evaluator, you personally hand-score 10–15 transcripts (can be from your own early test sessions) and compare your scores against the evaluator's output. You adjust the rubric and/or evaluator prompt until agreement is reasonably close. This is a one-time manual exercise for V1, not an ongoing automated system (that's V3).

**8. Voice adapter layer — fully decoupled from the interview engine.** The engine's contract is text in, text out — it has no knowledge of audio. The voice layer wraps it: `mic audio → streaming STT → text → [interview engine] → text → TTS → audio out`. Silence detection, audio buffering, and turn-taking logic live entirely in this layer. This decoupling means the engine can be developed and tested with typed text before any audio code is written, and a bug can always be isolated to "audio layer" or "engine" without ambiguity.

**9. Persistence — first-class entities.** Sessions, individual conversational turns, claims, evidence, state transitions, and evaluations are all their own tables with real foreign-key relationships — not one JSON blob per session. Every session/evaluation record also carries version tags (which model, which prompt version, which rubric version, which state-machine/policy version produced it), so later you can tell exactly what generated any given result and investigate regressions.

**10. Telemetry.** Every LLM call (and every state transition, validated or rejected) emits a structured event from your own code — call type, inputs/outputs, latency, version tags. These events are piped into Langfuse from the start as a trace viewer, so a multi-step bug (extraction → transition proposal → validation → question generation) can actually be inspected step by step instead of guessed at.

**11. Post-interview report.** Renders the evaluation output for the candidate (you): scores with cited evidence, what went well, what didn't, which resume claims were hard to defend, what to study next.

### V1 definition of done
You can run a full 30–45+ minute real voice interview against your actual resume and a real job description, and get a report whose scores you'd trust more than your own gut sense of how the interview went. You can also pull up the trace of any session and explain, from logged state transitions, exactly why Miki asked what it asked at each point.

---

# V2 — "Miki Knows Me"

### Goal
Interview #8–10 should be demonstrably smarter than interview #1 because of what Miki has learned about you across sessions — not just because the conversation transcript is longer.

### What's added on top of V1

**1. Persistent candidate memory (`candidate_facts`).** A new table storing individual facts about the candidate over time: the fact itself, a category (e.g. "distributed systems trade-offs"), a confidence score, references to the evidence that produced it, when it was first observed, and when it was last reinforced. This is the most novel and highest-value engineering piece in the entire project — it is not a vector database, it's a deliberately designed confidence/decay model.

**2. A written confidence/decay rule set — designed before any code.** Before building the table's write logic, you write down (as a design document) exactly how confidence changes over time: e.g., a weakness observed once is low confidence; observed across 3+ sessions, high confidence; a subsequent strong answer on the same topic reduces confidence in the "weak" fact rather than silently deleting it. This rule set is tested against synthetic multi-session scenarios before it's trusted on your real data.

**3. Memory write pipeline.** After each session, an LLM call proposes fact writes (new fact / reinforce existing / contradict existing) as structured output. Your hand-written rule set — not LLM judgment alone — decides how those proposals actually change stored confidence values. Contradictions are never silent overwrites; they're logged as explicit revisions.

**4. Memory retrieval into session start.** Before generating the opening question of a new interview, the engine queries `candidate_facts` for high-confidence weaknesses/strengths and injects them as structured context into the state machine's transition-proposal and question-generation calls — not as a growing block of prior transcript text pasted into the prompt.

**5. Company intelligence (lowest priority within V2, build last).** Given a company URL, fetch and extract relevant engineering/product context, cache it, and make it available as optional context for question generation only — never for evaluation scoring, since company facts shouldn't affect how a candidate is graded.

**6. Two additional interview modes as configurations, not new code paths.** "Resume Attack" (opens by selecting a resume claim, probes methodology/measurement/actual contribution, weights claim-defensibility heavily in its rubric) and "System Design" (opens from an ambiguous prompt rather than a claim, rubric weights scale-establishment, trade-off reasoning, failure isolation). Both reuse the exact same V1 state machine and engine — only the policy config and rubric differ. If a new mode requires new engine code rather than a new config, that's a signal the V1 engine wasn't built generically enough.

**7. Progress tracking.** Per-category score trends over multiple sessions and a "recurring weakness" surface — categories where `candidate_facts` shows sustained high-confidence weakness that hasn't improved — built as reporting/aggregation queries over data you already have, not new infrastructure.

### V2 definition of done
After 8–10 real sessions over several weeks, you can show, with actual `candidate_facts` data, specific evidence that a later interview asked different and better-targeted questions *because of* accumulated memory, and you can point to at least one real contradiction-handling event (a stored weakness that was revised because of new, better evidence).

---

# V3 — "Miki Trains Me"

### Goal
Close the loop: weakness detected → targeted practice generated → re-tested → improvement measured. Also: prove the evaluator itself is trustworthy over time, not just at the V1 calibration checkpoint.

### What's added on top of V2

**1. Interviewer meta-evaluation (build this first in V3, before anything flashy).** A maintained set of past transcripts with your own honest manual scores, periodically re-run through the current evaluator to check agreement over time. This is what catches evaluator drift as you change prompts, rubrics, or models — it's the part of the project almost nobody builds, and it's what proves "evidence-based evaluation" stays true rather than degrading silently.

**2. GitHub/project ingestion.** Clone a repo, extract structure (README, key modules, commit depth), and summarize into a "project profile" comparable in shape to the resume-claims structure from V1 — extending the same claim-extraction pattern to code instead of text. Treat this as its own mini-project; it's a materially harder retrieval/parsing problem than company intelligence.

**3. Project Defense mode.** Probes actual implementation choices found in the ingested repo, and can cross-reference resume claims against what the code actually shows (e.g., a claim of "built a RAG pipeline" checked against whether the repo contains one).

**4. Weakness → drill loop.** A `practice_targets` table derived automatically from `candidate_facts` (persistent, non-improving high-confidence weaknesses), surfaced as short, focused drill sessions (5–15 minutes, single topic) rather than full interviews.

**5. Optional streaming voice upgrades.** Barge-in/interruption handling and lower-latency streaming, only if the V1/V2 voice pipeline is already solid and this is genuinely the remaining bottleneck to realism — not pursued by default.

### V3 definition of done
You can point to a specific weakness Miki identified, the drill session it generated in response, a follow-up interview where that weakness measurably improved, and a meta-evaluation record showing evaluator scoring stayed consistent (or that you caught and fixed a drift) across the project's life.

---

## Cross-version guardrails (apply at every stage)

- Never build a new capability on top of one that hasn't been verified working. Text loop before voice. Rules on paper before rules in code. Manual calibration before automated calibration.
- Every "intelligent" output (a transition, a memory write, an evaluation) passes through a deterministic check before being trusted — never let the LLM's output be the final word on something structural.
- Default to the cheap model everywhere in the dev/iteration loop; upgrade specific call sites deliberately once their logic is proven correct and you're tuning for quality.
- The two most tempting things to over-invest in for visible-but-shallow progress are voice polish and company/GitHub research — both are explicitly sequenced late for a reason; protect time instead for the state-machine validator, the rubric, and the memory confidence model, which are less satisfying to build and are the actual differentiators.