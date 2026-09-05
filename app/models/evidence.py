from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import EvidenceType

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.turn import Turn


class Evidence(Base):
    """One observation about a claim, tied to the turn where it appeared.

    Produced alongside claims by the Phase 6 extraction call: each evidence
    row records what was actually said (``evidence_text``) and how it relates
    to the claim — ``supports`` (concrete detail backing it), ``contradicts``
    (conflicts with the claim or an earlier statement), or ``vague``
    (hand-waving that fails to substantiate it). The evaluator (Phase 11)
    cites these rows to justify every score.
    """

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Claim this evidence speaks to.
    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claim.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Turn where this evidence was observed.
    turn_id: Mapped[int] = mapped_column(
        ForeignKey("turn.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # What was actually said that constitutes this evidence.
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Relationship to the claim: "supports", "contradicts" or "vague".
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(
            EvidenceType,
            name="evidence_type",
            native_enum=False,
            # Persist lowercase values ("supports"/...), not member names.
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Parent claim and the turn where the evidence appeared.
    claim: Mapped["Claim"] = relationship("Claim", back_populates="evidence_items")
    turn: Mapped["Turn"] = relationship("Turn", back_populates="evidence_items")
