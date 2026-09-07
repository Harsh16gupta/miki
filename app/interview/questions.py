"""Question/probe generation for the validated state (Phase 8).

Unlike every other LLM call in the pipeline, this one returns user-facing
prose — not JSON. The prompt takes the validated state, the policy, the
target claim (when probing), and the candidate/role profiles, and produces
the next interview question. Callers persist it as a ``miki`` turn.
Uses ``task_type="question_generation"`` (strong model), no response format.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.interview.states import InterviewState
from app.llm.router import call_llm
from app.models import Claim, Turn
from app.models.enums import Speaker
from app.policy.loader import InterviewPolicy

SYSTEM_PROMPT = (
    "You are Miki, a sharp but fair technical interviewer. "
    "Write the single next interview question as plain prose — no JSON, "
    "no preamble, no bullet points, just the question (2-4 sentences max). "
    "Probe methodology, measurement, and actual contribution: ask HOW it was "
    "built, HOW the numbers were measured, and what the candidate personally "
    "did versus the team. Calibrate to the state: OPENING asks a broad "
    "warmer tied to the resume; PROBING_CLAIM attacks one specific claim; "
    "FOLLOWING_UP digs one level deeper into the last answer; ESCALATING "
    "raises difficulty (trade-offs, scale, failure modes); DE_ESCALATING "
    "drops to fundamentals with scaffolding; REDIRECTING moves to a new "
    "topic; CLOSING thanks the candidate and ends the interview."
)


def _context_block(
    state: InterviewState,
    policy: InterviewPolicy,
    candidate_json: dict[str, Any],
    role_json: dict[str, Any],
    target_claim: Claim | None,
    recent_turns: list[str],
) -> str:
    lines = [
        f"State: {state.value}",
        f"Target duration: {policy.target_duration_minutes}min. "
        f"Escalate: {policy.difficulty_escalation_rule} "
        f"De-escalate: {policy.difficulty_deescalation_rule}",
        "Candidate profile: "
        f"skills={candidate_json.get('skills', [])} "
        f"projects={candidate_json.get('projects', [])} "
        f"claims={candidate_json.get('claims', [])}",
        "Role profile: "
        f"required={role_json.get('required_skills', [])} "
        f"responsibilities={role_json.get('responsibilities', [])}",
    ]
    if target_claim is not None:
        lines.append(
            f"Target claim (id={target_claim.id}, "
            f"category={target_claim.category}): {target_claim.claim_text}"
        )
    else:
        lines.append("Target claim: (none — ask broadly)")
    if recent_turns:
        lines.append("Recent conversation:")
        lines.extend(f"- {t}" for t in recent_turns)
    else:
        lines.append("Recent conversation: (none yet)")
    return "\n".join(lines)


def generate_question(
    state: InterviewState,
    policy: InterviewPolicy,
    candidate_json: dict[str, Any],
    role_json: dict[str, Any],
    target_claim: Claim | None = None,
    recent_turns: list[str] | None = None,
) -> tuple[str, str]:
    """Generate the next question text. Returns (question, model_id)."""
    user_content = _context_block(
        state, policy, candidate_json, role_json, target_claim, recent_turns or []
    )
    result = call_llm(
        task_type="question_generation",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    question = (result["content"] or "").strip()
    if not question:
        raise ValueError("Question generation returned empty text")
    return question, result["model_id"]


def persist_miki_turn(db: DbSession, *, session_id: int, text: str) -> Turn:
    """Append Miki's question as the next turn in the session."""
    latest = (
        db.query(Turn)
        .filter(Turn.session_id == session_id)
        .order_by(Turn.turn_index.desc())
        .first()
    )
    next_index = (latest.turn_index + 1) if latest else 1
    turn = Turn(
        session_id=session_id,
        turn_index=next_index,
        speaker=Speaker.MIKI,
        text=text,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn
