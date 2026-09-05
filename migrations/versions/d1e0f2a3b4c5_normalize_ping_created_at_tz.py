"""normalize ping.created_at to timestamptz

Revision ID: d1e0f2a3b4c5
Revises: c5638748a60e
Create Date: 2026-09-06

Follows up the Ping model normalization (legacy ``Column`` style converted to
``Mapped[]`` with ``DateTime(timezone=True)``, consistent with every other
model). The ``ping`` table is a Phase 0 throwaway with no application code
depending on it; Postgres casts timestamp to timestamptz implicitly, so this
is a zero-risk type alignment picked up by ``alembic check``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e0f2a3b4c5"
down_revision: str | Sequence[str] | None = "c5638748a60e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "ping",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "ping",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
