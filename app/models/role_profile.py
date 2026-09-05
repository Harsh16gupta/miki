from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class RoleProfile(Base):
    """Structured view of one job description.

    Created by the Phase 3 ingestion pipeline: the raw JD text is stored
    verbatim in ``raw_jd_text``, and the LLM-extracted structure (required
    skills, preferred skills, responsibilities, seniority signal) is stored in
    ``extracted_json``. Like the candidate profile, the JSON blob is consumed
    as prompt context, never queried structurally.
    """

    __tablename__ = "role_profile"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Original job description text, exactly as uploaded/extracted (Phase 3).
    raw_jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    # LLM-extracted structure: required/preferred skills, responsibilities,
    # seniority signal.
    extracted_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # All interview sessions run against this profile. Deleting the profile
    # deletes its sessions (and everything under them) via cascade.
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="role_profile", cascade="all, delete-orphan"
    )
