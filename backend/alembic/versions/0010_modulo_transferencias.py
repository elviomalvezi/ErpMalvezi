"""modulo_transferencias

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-09

Cria a tabela: transferencia (movimentação atômica entre contas, intra e inter-empresa)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE status_transferencia AS ENUM ('concluida', 'cancelada')"
    )

    op.create_table(
        "transferencia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "empresa_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "empresa_destino_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conta_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conta_bancaria.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "conta_destino_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conta_bancaria.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_transferencia", sa.Date(), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_transferencia", create_type=False),
            nullable=False,
            server_default="concluida",
        ),
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
    op.create_index("ix_transferencia_empresa_origem", "transferencia", ["empresa_origem_id"])
    op.create_index("ix_transferencia_empresa_destino", "transferencia", ["empresa_destino_id"])
    op.create_index("ix_transferencia_data", "transferencia", ["data_transferencia"])
    op.create_index("ix_transferencia_conta_origem", "transferencia", ["conta_origem_id"])
    op.create_index("ix_transferencia_conta_destino", "transferencia", ["conta_destino_id"])


def downgrade() -> None:
    op.drop_index("ix_transferencia_conta_destino", table_name="transferencia")
    op.drop_index("ix_transferencia_conta_origem", table_name="transferencia")
    op.drop_index("ix_transferencia_data", table_name="transferencia")
    op.drop_index("ix_transferencia_empresa_destino", table_name="transferencia")
    op.drop_index("ix_transferencia_empresa_origem", table_name="transferencia")
    op.drop_table("transferencia")
    op.execute("DROP TYPE status_transferencia")
