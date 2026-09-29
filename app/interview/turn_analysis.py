"""Merged turn analysis: extraction + transition proposal in ONE LLM call.

Replaces the sequential ``extract_answer_claims`` -> ``propose_state`` pair
in the hot loop (saves a full provider round trip per turn — the dominant
cost on high-TTFT tiers). Returns a single JSON object::

    {"claims": [...same shape as extraction...],
     "proposed_state": "PROBING_CLAIM" | ...,
     "target_claim_id": int | null,
     "reason": "..."}

The deterministic :class:`StateMachine` still disposes: the proposal half
goes through ``apply_proposal`` exactly as before. Callers persist the
claims half with :func:`persist_answer_claims`.

Uses ``task_type="turn_analysis"`` (see ``model_config.yaml``).
"""

from __future__ import annotations

from typing import Any

import logging

from app.extraction.claims import _context_block as _answer_context_block
from app.interview.machine import TransitionContext
from app.interview.states import LEGAL_TRANSITIONS, InterviewState
from app.llm.router import call_llm
from app.models import Claim
from app.policy.loader import InterviewPolicy

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You do two jobs for an interview training system and return ONE JSON object. "
    "Job 1 — claim extractor: from the candidate's latest answer (plus recent "
    "conversation and resume claims) extract \"claims\": a list of objects, each with "
    "\"claim_text\" (one standalone sentence), "
    "\"category\" (short topic bucket, e.g. performance, system_design, "
    "communication, ownership), "
    "\"confidence\" (0.0-1.0: how strongly the answer substantiates it. "
    "Anchor strictly: 0.85-1.0 for assertions backed by concrete numbers "
    "AND method AND measurement (e.g. shard counts, before/after latencies, "
    "named tools); 0.7-0.84 for specific methods without hard numbers; "
    "0.4-0.69 for plausible but unmeasured detail; "
    "0.3 or lower for vague hand-waving with no specifics, and mark such "
    "evidence vague, never supports), "
    "\"contradicts_earlier\" (true if it conflicts with an earlier turn "
    "or a resume claim, else false), "
    "\"evidence\": a list of {\"evidence_text\" (exact quote or paraphrase), "
    "\"evidence_type\" (supports, contradicts, vague)}. "
    "A vague answer with no verifiable content yields an empty claims list. "
    "Job 2 — interview strategist: given the current state, policy, coverage, "
    "and the claims you just extracted, propose \"proposed_state\" (exactly one "
    "of the legal next states listed), \"target_claim_id\" (integer id of the "
    "claim to probe next — use the ids in Recent claims, or null when the move "
    "is not claim-specific), and \"reason\" (one sentence tying the choice to "
    "the policy and evidence). Prefer FOLLOWING_UP when the latest answer is "
    "vague. After 2 consecutive strong, specific answers in the same category "
    "you MUST propose ESCALATING (trade-offs, scale, failure modes), never "
    "another FOLLOWING_UP. Propose CLOSING only when the numbers show "
    "minimums met AND elapsed time passed the target. "
    "Return ONLY valid JSON with keys claims, proposed_state, "
    "target_claim_id, reason. No markdown."
)


def _snapshot_block(
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
        lines.append("Recent claims (from earlier turns; new ids assigned after):")
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


def analyze_turn(
    answer_text: str,
    current_state: InterviewState,
    policy: InterviewPolicy,
    recent_claims: list[Claim] | None = None,
    coverage: TransitionContext | None = None,
    recent_turns: list[str] | None = None,
    resume_claims: list[str] | None = None,
) -> tuple[dict[str, Any], str]:
    """Extract claims AND propose the next state in one call.

    Returns (parsed_json, model_id). Raises ValueError on malformed output.
    """
    if not answer_text or not answer_text.strip():
        raise ValueError("Cannot analyze an empty answer")
    user_content = (
        f"{_answer_context_block(recent_turns or [], resume_claims or [])}\n\n"
        f"Latest answer:\n{answer_text.strip()}\n\n"
        f"{_snapshot_block(current_state, policy, recent_claims or [], coverage or TransitionContext())}"
    )
    result = call_llm(
        task_type="turn_analysis",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict) or not isinstance(parsed.get("claims"), list):
        raise ValueError(f"Turn analysis did not return a claims list: {parsed!r}")
    if "proposed_state" not in parsed:
        raise ValueError(f"Turn analysis missing proposed_state: {parsed!r}")
    return parsed, result["model_id"]


def analyze_turn_robust(
    answer_text: str,
    current_state: InterviewState,
    policy: InterviewPolicy,
    recent_claims: list[Claim] | None = None,
    coverage: TransitionContext | None = None,
    recent_turns: list[str] | None = None,
    resume_claims: list[str] | None = None,
) -> tuple[dict[str, Any], str, bool]:
    """Merged analysis with fallback to the two-call path.

    Returns (parsed, model_id, used_fallback). The merged call wins on
    latency (one round trip); when it fails (e.g. spurious empty content),
    the smaller extraction + proposal calls run instead — same shapes, same
    validator downstream. Raises the LAST error if both paths fail.
    """
    try:
        parsed, model_id = analyze_turn(
            answer_text,
            current_state,
            policy,
            recent_claims=recent_claims,
            coverage=coverage,
            recent_turns=recent_turns,
            resume_claims=resume_claims,
        )
        return parsed, model_id, False
    except Exception as first_error:
        logger.warning("merged turn analysis failed, falling back: %s", first_error)
        from app.extraction import extract_answer_claims
        from app.interview.proposal import propose_state

        try:
            claims_part = extract_answer_claims(
                answer_text,
                recent_turns=recent_turns,
                resume_claims=resume_claims,
            )
            proposal, model_id = propose_state(
                current_state, policy, recent_claims or [], coverage
            )
            return {**claims_part, **proposal}, model_id, True
        except Exception:
            logger.exception("turn analysis fallback also failed")
            raise first_error from None
