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
    """One interview run linking a candidate profile to a role profile.

    Created by ``POST /session/start`` (Phase 9) and closed when the state
    machine reaches ``CLOSING``. ``mode`` selects the interview policy
    (V1 supports only ``"normal"``); ``status`` tracks the lifecycle
    (``in_progress``/``completed``/``aborted``). ``policy_version`` and
    ``engine_version`` stamp exactly which policy config and engine code
    produced the session, so any result can be traced back to what generated
    it for later regression analysis.
    """

    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Candidate being interviewed.
    candidate_profile_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False
    )
    # Role being interviewed for.
    role_profile_id: Mapped[int] = mapped_column(
        ForeignKey("role_profile.id", ondelete="CASCADE"), nullable=False
    )
    # Interview mode/policy name, e.g. "normal" (V1 has one mode only).
    mode: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)
    # Lifecycle state: "in_progress", "completed" or "aborted" (lowercase).
    status: Mapped[SessionStatus] = mapped_column(
        Enum(
            SessionStatus,
            name="session_status",
            native_enum=False,
            # Persist lowercase values ("in_progress"/...), not member names.
            values_callable=lambda e: [m.value for m in e],
        ),
        default=SessionStatus.IN_PROGRESS,
        nullable=False,
    )
    # When the interview started; ended_at is set on close/abort.
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Version of the interview policy config used (see Phase 4).
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    # Version of the interview engine code used.
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Profiles this session runs against.
    candidate_profile: Mapped["CandidateProfile"] = relationship(
        "CandidateProfile", back_populates="sessions"
    )
    role_profile: Mapped["RoleProfile"] = relationship(
        "RoleProfile", back_populates="sessions"
    )
    # Conversation turns in order; claims/evidence extracted from them;
    # every state transition (accepted or rejected); final evaluation scores.
    # All cascade: deleting a session deletes its whole subtree.
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
