from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class RoleProfile(Base):
    __tablename__ = "role_profile"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    raw_jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="role_profile", cascade="all, delete-orphan"
    )
