"""modulo_contas_bancarias

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-09

Cria a tabela: conta_bancaria (corrente, poupança, caixinha, aplicação, cartão de crédito)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE tipo_conta AS ENUM "
        "('corrente', 'poupanca', 'caixinha', 'aplicacao', 'cartao_credito')"
    )
    op.execute(
        "CREATE TYPE bandeira_cartao AS ENUM "
        "('visa', 'mastercard', 'elo', 'amex', 'hipercard', 'outro')"
    )

    op.create_table(
        "conta_bancaria",
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
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM(name="tipo_conta", create_type=False),
            nullable=False,
        ),
        sa.Column("banco", sa.String(100), nullable=True),
        sa.Column("agencia", sa.String(20), nullable=True),
        sa.Column("numero_conta", sa.String(30), nullable=True),
        sa.Column("digito", sa.String(5), nullable=True),
        sa.Column("saldo_inicial", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("data_saldo_inicial", sa.Date(), nullable=True),
        sa.Column(
            "bandeira",
            postgresql.ENUM(name="bandeira_cartao", create_type=False),
            nullable=True,
        ),
        sa.Column("limite", sa.Numeric(15, 2), nullable=True),
        sa.Column("dia_vencimento", sa.SmallInteger(), nullable=True),
        sa.Column("dia_fechamento", sa.SmallInteger(), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default="true"),
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
    op.create_index("ix_conta_bancaria_empresa", "conta_bancaria", ["empresa_id"])
    op.create_index("ix_conta_bancaria_usuario", "conta_bancaria", ["usuario_id"])
    op.create_index("ix_conta_bancaria_tipo", "conta_bancaria", ["tipo"])


def downgrade() -> None:
    op.drop_index("ix_conta_bancaria_tipo", table_name="conta_bancaria")
    op.drop_index("ix_conta_bancaria_usuario", table_name="conta_bancaria")
    op.drop_index("ix_conta_bancaria_empresa", table_name="conta_bancaria")
    op.drop_table("conta_bancaria")
    op.execute("DROP TYPE bandeira_cartao")
    op.execute("DROP TYPE tipo_conta")
