"""modulo_patrimonio

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-10

Cria tabelas: veiculo, imovel
(gestão patrimonial - veículos e imóveis)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE combustivel_veiculo AS ENUM "
        "('gasolina', 'etanol', 'flex', 'diesel', 'eletrico', 'hibrido', 'gnv')"
    )
    op.execute(
        "CREATE TYPE status_veiculo AS ENUM "
        "('ativo', 'vendido', 'sinistrado', 'inativo')"
    )
    op.execute(
        "CREATE TYPE tipo_imovel AS ENUM "
        "('casa', 'apartamento', 'terreno', 'sala_comercial', 'galpao', 'loja', 'outro')"
    )
    op.execute(
        "CREATE TYPE status_imovel AS ENUM "
        "('ativo', 'locado', 'vendido', 'em_reforma', 'inativo')"
    )

    op.create_table(
        "veiculo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("placa", sa.String(10), nullable=True),
        sa.Column("renavam", sa.String(20), nullable=True),
        sa.Column("chassi", sa.String(50), nullable=True),
        sa.Column("numero_motor", sa.String(50), nullable=True),
        sa.Column("marca", sa.String(100), nullable=False),
        sa.Column("modelo", sa.String(150), nullable=False),
        sa.Column("ano_fabricacao", sa.Integer, nullable=False),
        sa.Column("ano_modelo", sa.Integer, nullable=True),
        sa.Column("cor", sa.String(50), nullable=True),
        sa.Column("combustivel", postgresql.ENUM(name="combustivel_veiculo", create_type=False), nullable=True),
        sa.Column("valor_aquisicao", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_aquisicao", sa.Date, nullable=True),
        sa.Column("valor_mercado", sa.Numeric(15, 2), nullable=True),
        sa.Column("quilometragem", sa.Integer, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_veiculo", create_type=False),
            nullable=False,
            server_default="ativo",
        ),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_veiculo_empresa", "veiculo", ["empresa_id"])
    op.create_index("ix_veiculo_usuario", "veiculo", ["usuario_id"])

    op.create_table(
        "imovel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
        sa.Column("tipo", postgresql.ENUM(name="tipo_imovel", create_type=False), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=False),
        sa.Column("matricula", sa.String(100), nullable=True),
        sa.Column("inscricao_municipal", sa.String(50), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("logradouro", sa.String(300), nullable=True),
        sa.Column("numero", sa.String(10), nullable=True),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("area_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("area_construida", sa.Numeric(10, 2), nullable=True),
        sa.Column("valor_aquisicao", sa.Numeric(15, 2), nullable=False),
        sa.Column("data_aquisicao", sa.Date, nullable=True),
        sa.Column("valor_mercado", sa.Numeric(15, 2), nullable=True),
        sa.Column("valor_venal", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_imovel", create_type=False),
            nullable=False,
            server_default="ativo",
        ),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_imovel_empresa", "imovel", ["empresa_id"])
    op.create_index("ix_imovel_usuario", "imovel", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_imovel_usuario", "imovel")
    op.drop_index("ix_imovel_empresa", "imovel")
    op.drop_table("imovel")

    op.drop_index("ix_veiculo_usuario", "veiculo")
    op.drop_index("ix_veiculo_empresa", "veiculo")
    op.drop_table("veiculo")

    op.execute("DROP TYPE status_imovel")
    op.execute("DROP TYPE tipo_imovel")
    op.execute("DROP TYPE status_veiculo")
    op.execute("DROP TYPE combustivel_veiculo")
