"""modulo_conciliacao

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-09

Cria tabelas: importacao_bancaria, transacao_bancaria, regra_categorizacao
(conciliação bancária OFX/CSV com aprendizado de categorização)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE status_importacao AS ENUM ('processando', 'concluida', 'erro')"
    )
    op.execute(
        "CREATE TYPE status_transacao AS ENUM ('pendente', 'conciliada', 'ignorada')"
    )
    op.execute(
        "CREATE TYPE tipo_transacao AS ENUM ('credito', 'debito')"
    )

    op.create_table(
        "importacao_bancaria",
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
        sa.Column("nome_arquivo", sa.String(200), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_importacao", create_type=False),
            nullable=False,
            server_default="concluida",
        ),
        sa.Column("total_transacoes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conciliadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ignoradas", sa.Integer(), nullable=False, server_default="0"),
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
    op.create_index("ix_importacao_conta", "importacao_bancaria", ["conta_bancaria_id"])
    op.create_index("ix_importacao_usuario", "importacao_bancaria", ["usuario_id"])

    op.create_table(
        "transacao_bancaria",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "importacao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("importacao_bancaria.id", ondelete="CASCADE"),
            nullable=False,
        ),
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
        sa.Column("id_externo", sa.String(100), nullable=True),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM(name="tipo_transacao", create_type=False),
            nullable=False,
        ),
        sa.Column("descricao_original", sa.String(500), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_transacao", create_type=False),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "lancamento_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lancamento.id", ondelete="SET NULL"),
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
    )
    op.create_index("ix_transacao_importacao", "transacao_bancaria", ["importacao_id"])
    op.create_index("ix_transacao_conta", "transacao_bancaria", ["conta_bancaria_id"])
    op.create_index("ix_transacao_data", "transacao_bancaria", ["data"])
    op.create_index("ix_transacao_status", "transacao_bancaria", ["status"])

    op.create_table(
        "regra_categorizacao",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("padrao", sa.String(300), nullable=False),
        sa.Column(
            "categoria_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "tipo_lancamento",
            postgresql.ENUM(name="tipo_lancamento", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "contato_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contato.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contador", sa.Integer(), nullable=False, server_default="1"),
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
        sa.UniqueConstraint("usuario_id", "padrao", name="uq_regra_usuario_padrao"),
    )
    op.create_index("ix_regra_usuario", "regra_categorizacao", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_regra_usuario", table_name="regra_categorizacao")
    op.drop_table("regra_categorizacao")

    op.drop_index("ix_transacao_status", table_name="transacao_bancaria")
    op.drop_index("ix_transacao_data", table_name="transacao_bancaria")
    op.drop_index("ix_transacao_conta", table_name="transacao_bancaria")
    op.drop_index("ix_transacao_importacao", table_name="transacao_bancaria")
    op.drop_table("transacao_bancaria")

    op.drop_index("ix_importacao_usuario", table_name="importacao_bancaria")
    op.drop_index("ix_importacao_conta", table_name="importacao_bancaria")
    op.drop_table("importacao_bancaria")

    op.execute("DROP TYPE tipo_transacao")
    op.execute("DROP TYPE status_transacao")
    op.execute("DROP TYPE status_importacao")
