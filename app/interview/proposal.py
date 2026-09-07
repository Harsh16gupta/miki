"""LLM transition proposals, always validated before use (Phase 7).

The LLM *proposes* ``{proposed_state, target_claim_id, reason}``; the
deterministic :class:`StateMachine` *disposes*. Nothing here ever mutates
state directly — :func:`apply_proposal` is the only bridge, and it routes
every proposal through ``StateMachine.propose_transition``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.interview.machine import StateMachine, TransitionContext
from app.interview.states import LEGAL_TRANSITIONS, InterviewState
from app.llm.router import call_llm
from app.models import Claim, Session, StateTransition, Turn
from app.policy.loader import InterviewPolicy

SYSTEM_PROMPT = (
    "You are the strategist for an interview training system. "
    "Given the current interview state, the interview policy, recent claims "
    "and evidence, and coverage so far, propose the next state as a single "
    "JSON object with keys: "
    '"proposed_state" (exactly one of OPENING, PROBING_CLAIM, FOLLOWING_UP, '
    "ESCALATING, DE_ESCALATING, REDIRECTING, CLOSING), "
    '"target_claim_id" (integer id of the claim to probe next, or null when '
    "the move is not claim-specific), "
    '"reason" (one sentence tying the choice to the policy and evidence). '
    "Prefer FOLLOWING_UP when the latest answer is vague. After 2 "
    "consecutive strong, specific answers in the same category you MUST "
    "propose ESCALATING (a harder variant: trade-offs, scale, failure "
    "modes), never another FOLLOWING_UP. Propose CLOSING only when the "
    "numbers show minimums met AND elapsed time passed the target. "
    "Return ONLY valid JSON, no markdown."
)


def _snapshot_text(
    current_state: InterviewState,
    policy: InterviewPolicy,
    recent_claims: list[Claim],
    coverage: TransitionContext,
) -> str:
    lines = [
        f"Current state: {current_state.value}",
        "Legal next states from here (propose exactly one of these): "
        + ", ".join(sorted(s.value for s in LEGAL_TRANSITIONS[current_state])),
        "Policy: "
        f"target={policy.target_duration_minutes}min "
        f"(+{policy.max_overtime_minutes} overtime), "
        f"min_projects={policy.min_projects_covered}, "
        f"min_skills={policy.min_required_skills_covered}, "
        f"max_followups_per_claim={policy.max_followups_per_claim}; "
        f"escalate: {policy.difficulty_escalation_rule} "
        f"de-escalate: {policy.difficulty_deescalation_rule} "
        f"close: {policy.closing_rule}",
        "Coverage so far: "
        f"projects={coverage.projects_covered}, "
        f"skills={coverage.required_skills_covered}, "
        f"followups_on_claim={coverage.followups_on_current_claim}, "
        f"elapsed={coverage.elapsed_minutes:.1f}min",
    ]
    if recent_claims:
        lines.append("Recent claims:")
        for claim in recent_claims[-6:]:
            lines.append(
                f"- id={claim.id} [{claim.category} conf={claim.confidence:.2f}] "
                f"{claim.claim_text[:160]}"
            )
        streak = 0
        for claim in reversed(recent_claims):
            if claim.confidence >= 0.7:
                streak += 1
            else:
                break
        lines.append(
            f"Strong-answer streak (trailing claims with "
            f"confidence>=0.70): {streak}. Escalate at 2+."
        )
    else:
        lines.append("Recent claims: (none yet)")
    return "\n".join(lines)


def propose_state(
    current_state: InterviewState,
    policy: InterviewPolicy,
    recent_claims: list[Claim] | None = None,
    coverage: TransitionContext | None = None,
) -> tuple[dict[str, Any], str]:
    """Ask the LLM for the next state. Returns (proposal, model_id)."""
    snapshot = _snapshot_text(
        current_state, policy, recent_claims or [], coverage or TransitionContext()
    )
    result = call_llm(
        task_type="state_transition_proposal",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": snapshot},
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict) or "proposed_state" not in parsed:
        raise ValueError(f"Proposal missing proposed_state: {parsed!r}")
    return parsed, result["model_id"]


def context_for_session(
    db: DbSession, session: Session, policy: InterviewPolicy
) -> TransitionContext:
    """Assemble policy-gate facts for a session.

    Coverage attribution (claim -> project/skill) lands in the Phase 9 loop;
    until then projects/skills covered stay 0, which conservatively blocks
    early CLOSING — the safe direction for a validator.
    """
    elapsed = (datetime.now(UTC) - session.started_at).total_seconds() / 60.0
    followups = 0
    transitions = (
        db.query(StateTransition)
        .filter(StateTransition.session_id == session.id)
        .order_by(StateTransition.id.desc())
        .limit(10)
        .all()
    )
    for t in transitions:
        if t.to_state == InterviewState.FOLLOWING_UP.value and t.was_validated:
            followups += 1
        else:
            break
    return TransitionContext(
        followups_on_current_claim=followups,
        elapsed_minutes=max(0.0, elapsed),
        projects_covered=0,
        required_skills_covered=0,
    )


def recent_claims_for_session(
    db: DbSession, session_id: int, limit: int = 6
) -> list[Claim]:
    """Newest claims in a session, oldest-first for prompt readability."""
    rows = (
        db.query(Claim)
        .filter(Claim.session_id == session_id)
        .order_by(Claim.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def apply_proposal(
    machine: StateMachine,
    proposal: dict[str, Any],
    model_id: str,
    ctx: TransitionContext | None = None,
) -> bool:
    """Feed one proposal through the validator. Returns True if applied."""
    target = proposal.get("proposed_state")
    reason = str(proposal.get("reason", "") or "")[:500]
    return machine.propose_transition(
        str(target),
        reason or "no reason given",
        ctx,
        proposed_by_llm=True,
        model_id=model_id,
    )


def turn_count(db: DbSession, session_id: int) -> int:
    """Number of turns so far (used by later phases for loop control)."""
    return db.query(Turn).filter(Turn.session_id == session_id).count()
