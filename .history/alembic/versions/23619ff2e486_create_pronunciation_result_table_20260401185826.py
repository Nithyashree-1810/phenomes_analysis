from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '23619ff2e486'
down_revision = '5d3ea464050a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "pronunciation_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_text", sa.Text, nullable=False),
        sa.Column("transcript", sa.Text, nullable=False),
        sa.Column("phoneme_score", sa.Numeric(5, 2), default=0),
        sa.Column("fluency_score", sa.Numeric(5, 2), default=0),
        sa.Column("mistakes", JSONB, default=list),
        sa.Column("tips", JSONB, default=list),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table("pronunciation_result")