from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Speaker

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.evidence import Evidence
    from app.models.session import Session


class Turn(Base):
    """One message in an interview conversation.

    Both Miki's questions (``speaker="miki"``) and the candidate's answers
    (``speaker="candidate"``) are stored as turns, ordered per session by
    ``turn_index`` (1, 2, 3, ...). The voice layer (Phase 14) feeds
    transcribed speech into this same table, so the interview engine only ever
    deals with text turns regardless of input modality.
    """

    __tablename__ = "turn"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Session this turn belongs to.
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Position of the turn within its session, starting at 1.
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Who spoke: "candidate" or "miki" (stored lowercase, see enums.py).
    speaker: Mapped[Speaker] = mapped_column(
        Enum(
            Speaker,
            name="speaker",
            native_enum=False,
            # Persist lowercase values ("candidate"/"miki"), not member names.
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    # Full text of the question or answer.
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Parent session; claims and evidence extracted from this turn.
    session: Mapped["Session"] = relationship("Session", back_populates="turns")
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="turn", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="turn", cascade="all, delete-orphan"
    )
