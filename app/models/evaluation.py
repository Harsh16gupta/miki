from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Evaluation(Base):
    """One rubric-dimension score for a finished interview session.

    Produced by the Phase 11 evaluator (one row per dimension, e.g.
    ``"system_design"``): an LLM call scores the session against the rubric,
    and every score must cite the evidence behind it. ``evidence_refs`` holds
    the JSON array of evidence/claim/turn ids justifying the score, so any
    score can be traced back to the exact transcript moments behind it.
    ``rubric_version`` and ``model_id`` record exactly what produced the score
    for later regression analysis.
    """

    __tablename__ = "evaluation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Session this score belongs to (many rows per session, one per dimension).
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Rubric dimension being scored, e.g. "system_design".
    dimension: Mapped[str] = mapped_column(String(100), nullable=False)
    # Numeric score for the dimension (scale defined by the rubric config).
    score: Mapped[float] = mapped_column(Float, nullable=False)
    # Ids of the evidence/claim/turn rows justifying this score.
    evidence_refs: Mapped[list[int] | dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    # Version of the rubric config used (see Phase 11).
    rubric_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # Model that produced the score (e.g. "anthropic/claude-sonnet-4.5").
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Parent session; deleted automatically when the session is deleted.
    session: Mapped["Session"] = relationship(
        "Session", back_populates="evaluations"
    )
