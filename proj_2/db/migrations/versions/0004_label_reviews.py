"""label reviews: diet tags that ingredients contradict, for a person to decide (#18)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "label_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("dish", sa.String(300), nullable=False),
        sa.Column("item_name", sa.String(300), nullable=False),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("words", postgresql.JSONB(), nullable=False),
        sa.Column("ingredients_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.String(100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_label_reviews_status",
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_label_reviews_dish_ingredients",
        "label_reviews",
        ["location_id", "dish", "ingredients_hash"],
        unique=True,
    )


def downgrade():
    op.drop_table("label_reviews")
