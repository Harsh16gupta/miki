from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class CandidateProfile(Base):
    """Structured view of one candidate's resume.

    Created by the Phase 3 ingestion pipeline: the raw resume text is stored
    verbatim in ``raw_resume_text``, and the LLM-extracted structure (skills
    list, projects with descriptions, explicit claims such as "reduced latency
    by 40%") is stored in ``extracted_json``. The JSON blob is consumed as
    prompt context by later phases, never queried structurally, which is why
    it stays a blob instead of normalized tables.
    """

    __tablename__ = "candidate_profile"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Original resume text, exactly as uploaded/extracted (Phase 3).
    raw_resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    # LLM-extracted structure: skills, projects, explicit claims.
    extracted_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # All interview sessions run against this profile. Deleting the profile
    # deletes its sessions (and everything under them) via cascade.
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
