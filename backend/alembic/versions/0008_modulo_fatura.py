"""modulo_fatura

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-09

Cria a tabela: fatura (ciclo de vida da fatura de cartão de crédito)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE status_fatura AS ENUM ('aberta', 'fechada', 'paga')"
    )

    op.create_table(
        "fatura",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "conta_bancaria_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conta_bancaria.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("data_fechamento", sa.Date(), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_fatura", create_type=False),
            nullable=False,
            server_default="aberta",
        ),
        sa.Column("valor_total", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("valor_pago", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column(
            "conta_pagamento_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conta_bancaria.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conta_bancaria_id", "competencia", name="uq_fatura_conta_competencia"
        ),
    )
    op.create_index("ix_fatura_conta_bancaria", "fatura", ["conta_bancaria_id"])
    op.create_index("ix_fatura_empresa", "fatura", ["empresa_id"])
    op.create_index("ix_fatura_competencia", "fatura", ["competencia"])
    op.create_index("ix_fatura_status", "fatura", ["status"])


def downgrade() -> None:
    op.drop_index("ix_fatura_status", table_name="fatura")
    op.drop_index("ix_fatura_competencia", table_name="fatura")
    op.drop_index("ix_fatura_empresa", table_name="fatura")
    op.drop_index("ix_fatura_conta_bancaria", table_name="fatura")
    op.drop_table("fatura")
    op.execute("DROP TYPE status_fatura")
