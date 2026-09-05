"""Shared enum types used by the ORM models.

All enums here are ``StrEnum`` with lowercase string values (``"in_progress"``,
``"candidate"``, ``"supports"``, ...). The lowercase *values* are what gets
persisted to the database: every model column using these enums declares
``values_callable=lambda e: [m.value for m in e]`` so SQLAlchemy stores
``e.value`` instead of the default ``e.name`` (which would be uppercase like
``"IN_PROGRESS"`` and would not match the lowercase contract in ``todo.md``).
"""

from enum import StrEnum


class SessionStatus(StrEnum):
    """Lifecycle state of an interview session."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class Speaker(StrEnum):
    """Who produced a conversation turn: the candidate or Miki."""

    CANDIDATE = "candidate"
    MIKI = "miki"


class EvidenceType(StrEnum):
    """How a piece of evidence relates to the claim it is attached to."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    VAGUE = "vague"
