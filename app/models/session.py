from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.claim import Claim
    from app.models.evaluation import Evaluation
    from app.models.role_profile import RoleProfile
    from app.models.state_transition import StateTransition
    from app.models.turn import Turn


class Session(Base):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False
    )
    role_profile_id: Mapped[int] = mapped_column(
        ForeignKey("role_profile.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(
            SessionStatus,
            name="session_status",
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=SessionStatus.IN_PROGRESS,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile", back_populates="sessions"
    )
    role_profile: Mapped["RoleProfile"] = relationship(
        "RoleProfile", back_populates="sessions"
    )
    turns: Mapped[list["Turn"]] = relationship(
        "Turn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Turn.turn_index",
    )
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="session", cascade="all, delete-orphan"
    )
    state_transitions: Mapped[list["StateTransition"]] = relationship(
        "StateTransition", back_populates="session", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="session", cascade="all, delete-orphan"
    )
