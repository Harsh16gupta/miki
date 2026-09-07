"""Interview state machine package (Phase 5, no LLM).

The LLM proposes transitions (Phase 7); deterministic code here disposes.
"""

from app.interview.loop import (
    ENGINE_VERSION,
    answer_session,
    append_candidate_turn,
    compute_coverage,
    full_context,
    load_machine,
    recent_turn_texts,
    resolve_target_claim,
    start_session,
)
from app.interview.machine import StateMachine, TransitionContext
from app.interview.proposal import (
    apply_proposal,
    context_for_session,
    propose_state,
    recent_claims_for_session,
)
from app.interview.questions import generate_question, persist_miki_turn
from app.interview.states import LEGAL_TRANSITIONS, InterviewState

__all__ = [
    "ENGINE_VERSION",
    "LEGAL_TRANSITIONS",
    "InterviewState",
    "StateMachine",
    "TransitionContext",
    "answer_session",
    "append_candidate_turn",
    "apply_proposal",
    "compute_coverage",
    "apply_proposal",
    "context_for_session",
    "full_context",
    "generate_question",
    "load_machine",
    "persist_miki_turn",
    "propose_state",
    "recent_claims_for_session",
    "recent_turn_texts",
    "resolve_target_claim",
    "start_session",
]
