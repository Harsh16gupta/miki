"""Interview state machine package (Phase 5, no LLM).

The LLM proposes transitions (Phase 7); deterministic code here disposes.
"""

from app.interview.machine import StateMachine, TransitionContext
from app.interview.states import LEGAL_TRANSITIONS, InterviewState

__all__ = ["LEGAL_TRANSITIONS", "InterviewState", "StateMachine", "TransitionContext"]
