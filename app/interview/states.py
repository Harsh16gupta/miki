"""Interview states and the legal-transition table (Phase 5).

The table is explicit and exhaustive: any transition not listed here is
illegal and the validator rejects it. ``CLOSING`` is terminal.
"""

from __future__ import annotations

from enum import StrEnum


class InterviewState(StrEnum):
    """All states of the V1 interview state machine."""

    OPENING = "OPENING"
    PROBING_CLAIM = "PROBING_CLAIM"
    FOLLOWING_UP = "FOLLOWING_UP"
    ESCALATING = "ESCALATING"
    DE_ESCALATING = "DE_ESCALATING"
    REDIRECTING = "REDIRECTING"
    CLOSING = "CLOSING"


LEGAL_TRANSITIONS: dict[InterviewState, frozenset[InterviewState]] = {
    InterviewState.OPENING: frozenset({InterviewState.PROBING_CLAIM}),
    InterviewState.PROBING_CLAIM: frozenset(
        {
            InterviewState.PROBING_CLAIM,
            InterviewState.FOLLOWING_UP,
            InterviewState.ESCALATING,
            InterviewState.DE_ESCALATING,
            InterviewState.REDIRECTING,
            InterviewState.CLOSING,
        }
    ),
    InterviewState.FOLLOWING_UP: frozenset(
        {
            InterviewState.FOLLOWING_UP,
            InterviewState.PROBING_CLAIM,
            InterviewState.ESCALATING,
            InterviewState.DE_ESCALATING,
            InterviewState.REDIRECTING,
            InterviewState.CLOSING,
        }
    ),
    InterviewState.ESCALATING: frozenset(
        {
            InterviewState.FOLLOWING_UP,
            InterviewState.PROBING_CLAIM,
            InterviewState.REDIRECTING,
            InterviewState.CLOSING,
        }
    ),
    InterviewState.DE_ESCALATING: frozenset(
        {
            InterviewState.FOLLOWING_UP,
            InterviewState.PROBING_CLAIM,
            InterviewState.REDIRECTING,
            InterviewState.CLOSING,
        }
    ),
    InterviewState.REDIRECTING: frozenset(
        {
            InterviewState.PROBING_CLAIM,
            InterviewState.FOLLOWING_UP,
            InterviewState.CLOSING,
        }
    ),
    InterviewState.CLOSING: frozenset(),
}
