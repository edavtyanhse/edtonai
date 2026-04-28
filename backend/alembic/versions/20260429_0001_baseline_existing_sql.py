"""Baseline existing SQL migrations.

Revision ID: 20260429_0001
Revises:
Create Date: 2026-04-29

Existing databases should first apply the ordered SQL files in
``backend/db/migrations`` and then stamp this revision. New schema changes can
be added as normal Alembic revisions after this baseline.
"""

from collections.abc import Sequence

revision: str = "20260429_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = ("baseline",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
