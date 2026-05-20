"""modulo_contatos

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-09

Cria a tabela: contato (clientes e fornecedores, PJ/PF, global/específico)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE tipo_contato AS ENUM ('PJ', 'PF')")

    op.create_table(
        "contato",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("tipo", postgresql.ENUM(name="tipo_contato", create_type=False), nullable=False),
        sa.Column("documento", sa.String(14), nullable=False),
        sa.Column("nome_principal", sa.String(200), nullable=False),
        sa.Column("nome_alternativo", sa.String(200), nullable=True),
        sa.Column("eh_cliente", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("eh_fornecedor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escopo", sa.String(12), nullable=False, server_default="global"),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("celular", sa.String(20), nullable=True),
        sa.Column("site", sa.String(500), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("logradouro", sa.String(200), nullable=True),
        sa.Column("numero", sa.String(10), nullable=True),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("pais", sa.String(50), nullable=False, server_default="Brasil"),
        sa.Column("observacoes", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("usuario_id", "documento", name="uq_contato_usuario_documento"),
    )
    op.create_index("ix_contato_usuario", "contato", ["usuario_id"])
    op.create_index("ix_contato_empresa", "contato", ["empresa_id"])
    op.create_index("ix_contato_nome", "contato", ["nome_principal"])


def downgrade() -> None:
    op.drop_index("ix_contato_nome", table_name="contato")
    op.drop_index("ix_contato_empresa", table_name="contato")
    op.drop_index("ix_contato_usuario", table_name="contato")
    op.drop_table("contato")
    op.execute("DROP TYPE tipo_contato")
