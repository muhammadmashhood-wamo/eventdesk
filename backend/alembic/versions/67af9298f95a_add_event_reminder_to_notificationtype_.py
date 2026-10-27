"""add EVENT_REMINDER to notificationtype enum

Revision ID: 67af9298f95a
Revises: f1baab56e7d8
Create Date: 2026-10-23 16:23:41.075575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67af9298f95a'
down_revision: Union[str, Sequence[str], None] = 'f1baab56e7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'EVENT_REMINDER'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
