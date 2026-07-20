"""lancamento: vínculo com veículo e imóvel

Revision ID: 0023
Revises: 0022
Create Date: 2026-06-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lancamento",
        sa.Column("veiculo_id", UUID(as_uuid=True), sa.ForeignKey("veiculo.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "lancamento",
        sa.Column("imovel_id", UUID(as_uuid=True), sa.ForeignKey("imovel.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_lancamento_veiculo", "lancamento", ["veiculo_id"])
    op.create_index("ix_lancamento_imovel", "lancamento", ["imovel_id"])


def downgrade() -> None:
    op.drop_index("ix_lancamento_imovel", table_name="lancamento")
    op.drop_index("ix_lancamento_veiculo", table_name="lancamento")
    op.drop_column("lancamento", "imovel_id")
    op.drop_column("lancamento", "veiculo_id")
