"""User account model (Backend auth B2).

Table name is ``users`` (plural): ``user`` is a reserved keyword in
PostgreSQL and must not be used as a table name.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class User(Base):
    """Registered account owning zero or more interview sessions.

    Sessions keep ``user_id`` nullable so guest (unauthenticated) interviews
    continue to work exactly as before auth existed.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Lowercased on write; unique constraint enforced by the DB.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Sessions owned by this user. User deletion preserves history:
    # Session.user_id is SET NULL (see app/models/session.py).
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")
