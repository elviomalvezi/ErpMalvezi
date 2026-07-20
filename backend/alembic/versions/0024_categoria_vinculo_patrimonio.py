"""categoria: exigir_veiculo e exigir_imovel

Revision ID: 0024
Revises: 0023
Create Date: 2026-06-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "categoria",
        sa.Column("exigir_veiculo", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "categoria",
        sa.Column("exigir_imovel", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("categoria", "exigir_imovel")
    op.drop_column("categoria", "exigir_veiculo")
