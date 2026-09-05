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
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claim.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_id: Mapped[int] = mapped_column(
        ForeignKey("turn.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(
            EvidenceType,
            name="evidence_type",
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="evidence_items")
    turn: Mapped["Turn"] = relationship("Turn", back_populates="evidence_items")
