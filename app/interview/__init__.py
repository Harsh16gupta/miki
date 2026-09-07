"""Interview state machine package (Phase 5, no LLM).

The LLM proposes transitions (Phase 7); deterministic code here disposes.
"""

from app.interview.machine import StateMachine, TransitionContext
from app.interview.proposal import (
    apply_proposal,
    context_for_session,
    propose_state,
    recent_claims_for_session,
)
from app.interview.states import LEGAL_TRANSITIONS, InterviewState

__all__ = [
    "LEGAL_TRANSITIONS",
    "InterviewState",
    "StateMachine",
    "TransitionContext",
    "apply_proposal",
    "context_for_session",
    "propose_state",
    "recent_claims_for_session",
]
