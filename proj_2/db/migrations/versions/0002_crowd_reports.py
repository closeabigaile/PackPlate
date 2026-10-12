"""crowd reports: students' not busy / moderate / crowded reports

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "crowd_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("level IN ('not_busy', 'moderate', 'crowded')", name="ck_crowd_reports_level"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crowd_reports_location_id_created_at", "crowd_reports", ["location_id", "created_at"])


def downgrade():
    op.drop_table("crowd_reports")
