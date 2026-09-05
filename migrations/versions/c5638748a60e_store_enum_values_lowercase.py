"""store enum values as lowercase

Revision ID: c5638748a60e
Revises: 35e9475d9a7d
Create Date: 2026-09-05

Enum columns use native_enum=False (plain VARCHAR, Python-side validation only).
The models previously persisted Enum NAMES (e.g. 'IN_PROGRESS') because no
values_callable was set. Models now use values_callable so they persist Enum
VALUES (e.g. 'in_progress'), matching the spec in todo.md. This migration
rewrites existing rows; no schema change is needed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5638748a60e"
down_revision: str | Sequence[str] | None = "35e9475d9a7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # session.status
    op.execute(
        sa.text("UPDATE session SET status='in_progress' WHERE status='IN_PROGRESS'")
    )
    op.execute(
        sa.text("UPDATE session SET status='completed' WHERE status='COMPLETED'")
    )
    op.execute(sa.text("UPDATE session SET status='aborted' WHERE status='ABORTED'"))
    # turn.speaker
    op.execute(sa.text("UPDATE turn SET speaker='candidate' WHERE speaker='CANDIDATE'"))
    op.execute(sa.text("UPDATE turn SET speaker='miki' WHERE speaker='MIKI'"))
    # evidence.evidence_type
    op.execute(
        sa.text(
            "UPDATE evidence SET evidence_type='supports' "
            "WHERE evidence_type='SUPPORTS'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE evidence SET evidence_type='contradicts' "
            "WHERE evidence_type='CONTRADICTS'"
        )
    )
    op.execute(
        sa.text("UPDATE evidence SET evidence_type='vague' WHERE evidence_type='VAGUE'")
    )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE session SET status='IN_PROGRESS' WHERE status='in_progress'")
    )
    op.execute(
        sa.text("UPDATE session SET status='COMPLETED' WHERE status='completed'")
    )
    op.execute(sa.text("UPDATE session SET status='ABORTED' WHERE status='aborted'"))
    op.execute(sa.text("UPDATE turn SET speaker='CANDIDATE' WHERE speaker='candidate'"))
    op.execute(sa.text("UPDATE turn SET speaker='MIKI' WHERE speaker='miki'"))
    op.execute(
        sa.text(
            "UPDATE evidence SET evidence_type='SUPPORTS' "
            "WHERE evidence_type='supports'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE evidence SET evidence_type='CONTRADICTS' "
            "WHERE evidence_type='contradicts'"
        )
    )
    op.execute(
        sa.text("UPDATE evidence SET evidence_type='VAGUE' WHERE evidence_type='vague'")
    )
