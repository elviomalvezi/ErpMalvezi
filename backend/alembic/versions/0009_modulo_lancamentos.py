"""modulo_lancamentos

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-09

Cria a tabela: lancamento (contas a pagar e a receber, parcelamento, recorrência)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE tipo_lancamento AS ENUM ('RECEITA', 'DESPESA')"
    )
    op.execute(
        "CREATE TYPE status_lancamento AS ENUM ('pendente', 'pago', 'cancelado')"
    )
    op.execute(
        "CREATE TYPE frequencia_recorrencia AS ENUM "
        "('semanal', 'quinzenal', 'mensal', 'anual')"
    )

    op.create_table(
        "lancamento",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column(
            "tipo",
            postgresql.ENUM(name="tipo_lancamento", create_type=False),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(300), nullable=False),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("valor_pago", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("data_competencia", sa.Date(), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_lancamento", create_type=False),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "categoria_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "contato_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contato.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "conta_bancaria_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conta_bancaria.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "fatura_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fatura.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("numero_parcela", sa.SmallInteger(), nullable=True),
        sa.Column("total_parcelas", sa.SmallInteger(), nullable=True),
        sa.Column("grupo_parcelas_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recorrencia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
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
    )
    op.create_index(
        "ix_lancamento_empresa_vencimento", "lancamento", ["empresa_id", "data_vencimento"]
    )
    op.create_index("ix_lancamento_status", "lancamento", ["status"])
    op.create_index("ix_lancamento_categoria", "lancamento", ["categoria_id"])
    op.create_index("ix_lancamento_contato", "lancamento", ["contato_id"])
    op.create_index("ix_lancamento_grupo", "lancamento", ["grupo_parcelas_id"])
    op.create_index("ix_lancamento_recorrencia", "lancamento", ["recorrencia_id"])


def downgrade() -> None:
    op.drop_index("ix_lancamento_recorrencia", table_name="lancamento")
    op.drop_index("ix_lancamento_grupo", table_name="lancamento")
    op.drop_index("ix_lancamento_contato", table_name="lancamento")
    op.drop_index("ix_lancamento_categoria", table_name="lancamento")
    op.drop_index("ix_lancamento_status", table_name="lancamento")
    op.drop_index("ix_lancamento_empresa_vencimento", table_name="lancamento")
    op.drop_table("lancamento")
    op.execute("DROP TYPE frequencia_recorrencia")
    op.execute("DROP TYPE status_lancamento")
    op.execute("DROP TYPE tipo_lancamento")
