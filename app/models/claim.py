from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.session import Session
    from app.models.turn import Turn


class Claim(Base):
    """One factual assertion extracted from a candidate's answer.

    Produced by the Phase 6 claim/evidence extraction LLM call after every
    candidate turn: each verifiable statement (e.g. "handled 10k req/s with
    partitioned queues") becomes a row linked to both the session and the
    exact turn it came from. ``category`` groups the claim by topic (e.g.
    "performance") and ``confidence`` records how strongly the answer supports
    it (low values flag vague answers for follow-up). Downstream, the state
    machine (Phase 7) and the evaluator (Phase 11) both reason over these rows.
    """

    __tablename__ = "claim"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Session this claim belongs to.
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Turn the claim was extracted from (always a candidate turn).
    turn_id: Mapped[int] = mapped_column(
        ForeignKey("turn.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The asserted statement, normalized to a standalone sentence.
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Topic bucket for the claim, e.g. "performance".
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # Extraction confidence 0.0-1.0; low values signal vague answers.
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Parent session and source turn; supporting/contradicting evidence rows.
    session: Mapped["Session"] = relationship("Session", back_populates="claims")
    turn: Mapped["Turn"] = relationship("Turn", back_populates="claims")
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="claim", cascade="all, delete-orphan"
    )
