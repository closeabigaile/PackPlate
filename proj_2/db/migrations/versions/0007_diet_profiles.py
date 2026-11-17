"""saved dietary profiles for logged-in users (M5)

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "diet_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=True),
        sa.Column("avoid", postgresql.JSONB(), nullable=False),
        sa.Column("diets", postgresql.JSONB(), nullable=False),
        sa.Column("min_protein_g", sa.Float(), nullable=True),
        sa.Column("max_calories", sa.Float(), nullable=True),
        sa.Column("max_sodium_mg", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade():
    op.drop_table("diet_profiles")
