from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '23619ff2e486'
down_revision = '5d3ea464050a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "pronunciation_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_text", sa.String, nullable=False),
        sa.Column("transcript", sa.String, nullable=False),
        sa.Column("phoneme_score", sa.Numeric(5,2)),
        sa.Column("fluency_score", sa.Numeric(5,2)),
        sa.Column("mistakes", JSONB, default=list),
        sa.Column("tips", JSONB, default=list),
        sa.Column("next_question", JSONB, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table("pronunciation_result")