"""create phoneme_performance table

Revision ID: 5d3ea464050a
Revises: 8f7f946a9a59
Create Date: 2026-04-01 16:43:12.519520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d3ea464050a'
down_revision: Union[str, Sequence[str], None] = '8f7f946a9a59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'new_revision_id'
down_revision = '8f7f946a9a59'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'phoneme_performance',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user_pronunciation_profile.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('phoneme', sa.String(length=50), nullable=False),
        sa.Column('total_attempts', sa.Integer(), default=0),
        sa.Column('correct_attempts', sa.Integer(), default=0),
        sa.Column('accuracy_pct', sa.Numeric(5, 2), default=0),
        sa.Column('last_attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'phoneme', name='uq_user_phoneme')
    )

def downgrade():
    op.drop_table('phoneme_performance')