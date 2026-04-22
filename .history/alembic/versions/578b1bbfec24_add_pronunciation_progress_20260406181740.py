"""add pronunciation progress

Revision ID: 578b1bbfec24
Revises: 6972abf32e98
Create Date: 2026-04-06 18:16:55.045990

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '578b1bbfec24'
down_revision: Union[str, Sequence[str], None] = '6972abf32e98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
