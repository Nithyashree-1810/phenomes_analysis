"""create pronunciation_result table

Revision ID: efc85a9dd239
Revises: 23619ff2e486
Create Date: 2026-04-01 19:00:22.028388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efc85a9dd239'
down_revision: Union[str, Sequence[str], None] = '23619ff2e486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
