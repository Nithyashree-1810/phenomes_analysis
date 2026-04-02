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
    op.create_table(
        "pronunciation_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_text", sa.Text, nullable=False),
        sa.Column("transcript", sa.Text, nullable=False),
        sa.Column("phoneme_score", sa.Numeric(5,2), default=0),
        sa.Column("fluency_score", sa.Numeric(5,2), default=0),
        sa.Column("mistakes", JSONB, default=list),
        sa.Column("tips", JSONB, default=list),
        sa.Column("next_question", JSONB, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table("pronunciation_result")
