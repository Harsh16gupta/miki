"""Full text interview loop engine (Phase 9).

One answer flows through: save candidate turn -> extract claims ->
propose transition -> validate -> generate next question -> persist it.
State is never kept in memory between calls: :func:`load_machine`
rebuilds the validator from the last validated ``state_transition`` row,
so the engine is stateless across HTTP requests and every decision is
traceable in the database.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.extraction import extract_answer_claims, persist_answer_claims
from app.interview.machine import StateMachine, TransitionContext
from app.interview.proposal import (
    apply_proposal,
    context_for_session,
    propose_state,
    recent_claims_for_session,
)
from app.interview.questions import generate_question, persist_miki_turn
from app.interview.states import InterviewState
from app.models import Claim, Session, StateTransition, Turn
from app.models.enums import SessionStatus, Speaker
from app.policy.loader import InterviewPolicy

logger = logging.getLogger(__name__)

ENGINE_VERSION = "0.1.0"

_WORD_RE = re.compile(r"[a-z]{4,}")


def load_machine(
    db: DbSession, session_id: int, policy: InterviewPolicy
) -> StateMachine:
    """Rebuild the validator from the last validated transition (or OPENING)."""
    last = (
        db.query(StateTransition)
        .filter(
            StateTransition.session_id == session_id,
            StateTransition.was_validated.is_(True),
        )
        .order_by(StateTransition.id.desc())
        .first()
    )
    current = InterviewState(last.to_state) if last else InterviewState.OPENING
    return StateMachine(session_id, db, policy, current_state=current)


def recent_turn_texts(db: DbSession, session_id: int, limit: int = 6) -> list[str]:
    """Last turns formatted for prompts, oldest-first."""
    rows = (
        db.query(Turn)
        .filter(Turn.session_id == session_id)
        .order_by(Turn.turn_index.desc())
        .limit(limit)
        .all()
    )
    out = []
    for turn in reversed(rows):
        who = "Miki" if turn.speaker == Speaker.MIKI else "Candidate"
        out.append(f"{who}: {turn.text}")
    return out


def _significant_words(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def compute_coverage(
    db: DbSession, session: Session, policy: InterviewPolicy
) -> tuple[int, int]:
    """V1 heuristic: a project/skill counts as covered when one of its
    significant words (4+ letters) appears in any claim or turn text.

    Crude but transparent; later versions attribute claims to
    projects/skills structurally instead of by word overlap.
    """
    _ = policy
    texts = " ".join(
        [c.claim_text for c in session.claims] + [t.text for t in session.turns]
    ).lower()
    words = _significant_words(texts)
    cand_json: dict[str, Any] = session.candidate_profile.extracted_json or {}
    role_json: dict[str, Any] = session.role_profile.extracted_json or {}

    projects_hit = 0
    for proj in cand_json.get("projects", []):
        name = proj.get("name", "") if isinstance(proj, dict) else str(proj)
        if _significant_words(name) & words:
            projects_hit += 1

    skills_hit = 0
    for skill in role_json.get("required_skills", []):
        if _significant_words(str(skill)) & words:
            skills_hit += 1
    return projects_hit, skills_hit


def full_context(
    db: DbSession, session: Session, policy: InterviewPolicy
) -> TransitionContext:
    """Policy-gate facts with real coverage numbers (not zeros)."""
    base = context_for_session(db, session, policy)
    projects, skills = compute_coverage(db, session, policy)
    return TransitionContext(
        followups_on_current_claim=base.followups_on_current_claim,
        elapsed_minutes=base.elapsed_minutes,
        projects_covered=projects,
        required_skills_covered=skills,
    )


def append_candidate_turn(db: DbSession, *, session_id: int, text: str) -> Turn:
    """Append the candidate's answer as the next turn."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Answer text must be non-empty")
    latest = (
        db.query(Turn)
        .filter(Turn.session_id == session_id)
        .order_by(Turn.turn_index.desc())
        .first()
    )
    turn = Turn(
        session_id=session_id,
        turn_index=(latest.turn_index + 1) if latest else 1,
        speaker=Speaker.CANDIDATE,
        text=cleaned,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def resolve_target_claim(
    db: DbSession, session_id: int, proposal: dict[str, Any]
) -> Claim | None:
    """Claim the proposal points at, else the newest claim, else None."""
    raw_id = proposal.get("target_claim_id")
    if isinstance(raw_id, int):
        claim = (
            db.query(Claim)
            .filter(Claim.session_id == session_id, Claim.id == raw_id)
            .first()
        )
        if claim is not None:
            return claim
    return (
        db.query(Claim)
        .filter(Claim.session_id == session_id)
        .order_by(Claim.id.desc())
        .first()
    )


def start_session(
    db: DbSession,
    *,
    candidate_profile_id: int,
    role_profile_id: int,
    policy: InterviewPolicy,
    user_id: int | None = None,
) -> tuple[Session, Turn]:
    """Create the session row and generate the opening question."""
    session = Session(
        candidate_profile_id=candidate_profile_id,
        role_profile_id=role_profile_id,
        mode=policy.mode,
        policy_version=policy.version,
        engine_version=ENGINE_VERSION,
        user_id=user_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    question, _ = generate_question(
        InterviewState.OPENING,
        policy,
        session.candidate_profile.extracted_json or {},
        session.role_profile.extracted_json or {},
    )
    first_turn = persist_miki_turn(db, session_id=session.id, text=question)
    logger.info("session %d started (policy %s)", session.id, policy.version)
    return session, first_turn


def answer_session(
    db: DbSession,
    session: Session,
    policy: InterviewPolicy,
    answer_text: str,
    ctx_override: TransitionContext | None = None,
) -> dict[str, Any]:
    """Run one full loop iteration. Returns the API-facing result dict."""
    if session.status != SessionStatus.IN_PROGRESS:
        raise ValueError(f"Session {session.id} is {session.status.value}, closed")

    machine = load_machine(db, session.id, policy)
    turn = append_candidate_turn(db, session_id=session.id, text=answer_text)
    db.refresh(session)

    resume_claims = (session.candidate_profile.extracted_json or {}).get("claims", [])
    parsed = extract_answer_claims(
        turn.text,
        recent_turns=recent_turn_texts(db, session.id),
        resume_claims=resume_claims if isinstance(resume_claims, list) else [],
    )
    claims = persist_answer_claims(
        db, session_id=session.id, turn_id=turn.id, parsed=parsed
    )
    db.refresh(session)

    ctx = ctx_override or full_context(db, session, policy)
    recent = recent_claims_for_session(db, session.id)
    proposal, model_id = propose_state(machine.current_state, policy, recent, ctx)
    applied = apply_proposal(machine, proposal, model_id, ctx)

    if machine.current_state == InterviewState.CLOSING and applied:
        session.status = SessionStatus.COMPLETED
        session.ended_at = datetime.now(UTC)
        db.commit()
        closer, _ = generate_question(
            InterviewState.CLOSING,
            policy,
            session.candidate_profile.extracted_json or {},
            session.role_profile.extracted_json or {},
            target_claim=None,
            recent_turns=recent_turn_texts(db, session.id),
        )
        closing_turn = persist_miki_turn(db, session_id=session.id, text=closer)
        logger.info("session %d closed (%d turns)", session.id, closing_turn.turn_index)
        try:
            from app.evaluation import evaluate_if_unscored, get_normal_rubric

            evaluate_if_unscored(db, session, get_normal_rubric())
        except Exception:
            logger.exception("session %d: eval failed, closing anyway", session.id)
        return {
            "question": closer,
            "state": InterviewState.CLOSING.value,
            "finished": True,
            "transition_applied": True,
            "claims_found": len(claims),
        }

    target = resolve_target_claim(db, session.id, proposal)
    question, _ = generate_question(
        machine.current_state,
        policy,
        session.candidate_profile.extracted_json or {},
        session.role_profile.extracted_json or {},
        target_claim=target,
        recent_turns=recent_turn_texts(db, session.id),
    )
    persist_miki_turn(db, session_id=session.id, text=question)
    return {
        "question": question,
        "state": machine.current_state.value,
        "finished": False,
        "transition_applied": applied,
        "claims_found": len(claims),
    }
