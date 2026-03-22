"""Sync with existing manual tables

Revision ID: 52dc17018616
Revises: bc37eee8fe67
Create Date: 2026-03-20 23:03:44.211003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52dc17018616'
down_revision: Union[str, Sequence[str], None] = 'bc37eee8fe67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
