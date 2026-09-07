from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class StateTransition(Base):
    """Audit record of one state-machine transition attempt.

    Core to the architecture principle that the LLM *proposes* but
    deterministic code *disposes*: the transition-proposal call (Phase 7)
    suggests ``to_state``, the ``StateMachine`` validator (Phase 5) checks it
    against the legal-transition table and policy config, and the outcome is
    recorded here either way. ``proposed_by_llm`` distinguishes LLM proposals
    from hardcoded ones (e.g. tests); ``was_validated`` tells whether the
    proposal was accepted; ``rejection_reason`` explains rejections.
    ``model_id`` records which model made the proposal for traceability.
    """

    __tablename__ = "state_transition"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Session this transition belongs to.
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # State before the proposal (e.g. "OPENING").
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    # Proposed state (e.g. "PROBING_CLAIM"); applied only if validated.
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)
    # True when the proposal came from the LLM, False for hardcoded/test ones.
    proposed_by_llm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # True when the validator accepted the proposal and applied it.
    was_validated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Why the proposal was rejected; None when accepted.
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Model that made the proposal (e.g. "deepseek/deepseek-chat").
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Parent session; deleted automatically when the session is deleted.
    session: Mapped["Session"] = relationship(
        "Session", back_populates="state_transitions"
    )
