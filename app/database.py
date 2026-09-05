"""Database engine, session factory, and declarative base.

All ORM models in ``app.models`` inherit from :class:`Base`, and all database
access goes through :data:`SessionLocal`. The connection URL is read from the
``DATABASE_URL`` environment variable (see ``.env.example``).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env so DATABASE_URL (and other secrets) are available via os.getenv.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fail fast with a clear message instead of a cryptic SQLAlchemy error
    # from create_engine(None) later.
    raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and set it.")

# pool_pre_ping=True makes the pool test connections before checkout, so a
# dropped connection (e.g. Postgres container restarted) raises a clean,
# retryable error instead of handing out a dead connection.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Per-request session factory. Callers must close the session when done
# (e.g. via FastAPI dependency with try/finally or context manager).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models in this project."""

    pass
