"""modulo_empresa

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09

Cria as tabelas: usuario, empresa, usuario_empresa
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tipos ENUM
    op.execute("CREATE TYPE tipo_pessoa AS ENUM ('PJ', 'PF')")
    op.execute("CREATE TYPE regime_tributario AS ENUM ('Simples', 'Presumido', 'Real', 'MEI')")

    # ── usuario ────────────────────────────────────────────────────────────
    op.create_table(
        "usuario",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("foto_url", sa.String(500), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_verificado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "preferencia_multi_empresa", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("ultimo_login_em", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_usuario_email"),
    )

    # ── empresa ────────────────────────────────────────────────────────────
    op.create_table(
        "empresa",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", postgresql.ENUM(name="tipo_pessoa", create_type=False), nullable=False),
        sa.Column("documento", sa.String(18), nullable=False),
        sa.Column("nome_principal", sa.String(200), nullable=False),
        sa.Column("nome_alternativo", sa.String(200), nullable=True),
        sa.Column("documento_complementar_1", sa.String(30), nullable=True),
        sa.Column("documento_complementar_2", sa.String(30), nullable=True),
        sa.Column(
            "regime_tributario",
            postgresql.ENUM(name="regime_tributario", create_type=False),
            nullable=True,
        ),
        # Configurações monetárias
        sa.Column("moeda_padrao", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("simbolo_monetario", sa.String(5), nullable=False, server_default="R$"),
        sa.Column("separador_decimal", sa.String(1), nullable=False, server_default=","),
        sa.Column("separador_milhares", sa.String(1), nullable=False, server_default="."),
        sa.Column("casas_decimais_valor", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column(
            "casas_decimais_percentual", sa.SmallInteger(), nullable=False, server_default="2"
        ),
        # Configurações financeiras
        sa.Column("mes_inicio_exercicio", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column(
            "trava_fechamento_ativa", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("dia_fechamento_mensal", sa.SmallInteger(), nullable=False, server_default="5"),
        sa.Column("prefixo_lancamento", sa.String(10), nullable=False, server_default="LCT-"),
        sa.Column(
            "proximo_numero_lancamento", sa.BigInteger(), nullable=False, server_default="1"
        ),
        sa.Column(
            "reset_anual_numeracao", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("data_inicio_uso", sa.Date(), nullable=True),
        # Identidade visual
        sa.Column("cor_primaria", sa.String(7), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("email_remetente_nome", sa.String(200), nullable=True),
        sa.Column("email_assinatura", sa.Text(), nullable=True),
        sa.Column("mensagem_padrao_boleto", sa.Text(), nullable=True),
        # Endereço
        sa.Column("endereco_cep", sa.String(9), nullable=True),
        sa.Column("logradouro", sa.String(200), nullable=True),
        sa.Column("numero", sa.String(10), nullable=True),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("pais", sa.String(50), nullable=False, server_default="Brasil"),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "criado_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="SET NULL"),
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
        sa.UniqueConstraint("documento", name="uq_empresa_documento"),
    )
    op.create_index("idx_empresa_ativa", "empresa", ["ativa"])

    # ── usuario_empresa ────────────────────────────────────────────────────
    op.create_table(
        "usuario_empresa",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
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
        sa.UniqueConstraint("usuario_id", "empresa_id", name="uq_usuario_empresa"),
    )
    op.create_index("idx_usuario_empresa_usuario", "usuario_empresa", ["usuario_id"])
    op.create_index("idx_usuario_empresa_empresa", "usuario_empresa", ["empresa_id"])


def downgrade() -> None:
    op.drop_table("usuario_empresa")
    op.drop_index("idx_empresa_ativa", table_name="empresa")
    op.drop_table("empresa")
    op.drop_table("usuario")

    op.execute("DROP TYPE IF EXISTS tipo_pessoa")
    op.execute("DROP TYPE IF EXISTS regime_tributario")
