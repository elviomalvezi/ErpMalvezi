"""lancamento tags

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lancamento",
        sa.Column(
            "tags",
            ARRAY(sa.String(50)),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("lancamento", "tags")
