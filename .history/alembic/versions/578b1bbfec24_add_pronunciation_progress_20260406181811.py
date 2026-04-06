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
    op.create_table(
        'user_pronunciation_progress',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('total_levels', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('current_level', sa.String(20), nullable=False, server_default='beginner'),
        sa.Column('completion_pct', sa.Numeric(5, 2), server_default='0'),
        sa.Column('avg_score', sa.Numeric(5, 2), server_default='0'),
        sa.Column('weak_phonemes', JSONB, server_default='[]'),
        sa.Column('time_spent_mins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
