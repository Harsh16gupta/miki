from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Ping(Base):
    """Throwaway Phase 0 sanity-check table.

    Created only to prove the SQLAlchemy -> Alembic -> Postgres pipeline works
    end to end before the real schema existed. Not used by any application
    code; kept for the migration history to stay consistent.
    """

    __tablename__ = "ping"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
