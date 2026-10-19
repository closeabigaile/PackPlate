"""ingredient flags: possible allergens named in a label's ingredients (issue #15)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # Existing labels start empty ({}); ingestion fills the column.
    op.add_column(
        "nutrition",
        sa.Column(
            "ingredient_flags",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade():
    op.drop_column("nutrition", "ingredient_flags")
