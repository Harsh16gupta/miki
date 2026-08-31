from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer

from app.database import Base


class Ping(Base):
    __tablename__ = "ping"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
