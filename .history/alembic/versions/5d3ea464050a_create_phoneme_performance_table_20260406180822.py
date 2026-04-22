"""create phoneme_performance table

Revision ID: 5d3ea464050a
Revises: 8f7f946a9a59
Create Date: 2026-04-01 16:43:12.519520
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5d3ea464050a'
down_revision: Union[str, Sequence[str], None] = '8f7f946a9a59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass