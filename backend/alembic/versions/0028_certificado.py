"""certificado: cadastro e controle de vencimento de certificados

Cria a tabela `certificado` (ICP-Brasil e SSL) com metadados, arquivo (BYTEA) e
senha cifrada, para importação e gestão de vencimentos.

Revision ID: 0028
Revises: 0027
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_enum = postgresql.ENUM(
        "e_cnpj", "e_cpf", "ssl", "outro", name="tipo_certificado"
    )
    tipo_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "certificado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM(
                "e_cnpj", "e_cpf", "ssl", "outro",
                name="tipo_certificado", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("titular", sa.String(300), nullable=True),
        sa.Column("documento", sa.String(20), nullable=True),
        sa.Column("emissor", sa.String(300), nullable=True),
        sa.Column("numero_serie", sa.String(100), nullable=True),
        sa.Column("validade_inicio", sa.Date(), nullable=True),
        sa.Column("validade_fim", sa.Date(), nullable=True),
        sa.Column("formato", sa.String(10), nullable=True),
        sa.Column("arquivo_nome", sa.String(255), nullable=True),
        sa.Column("arquivo", sa.LargeBinary(), nullable=True),
        sa.Column("senha_cifrada", sa.Text(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "atualizado_em", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_certificado_empresa", "certificado", ["empresa_id"])
    op.create_index("ix_certificado_validade_fim", "certificado", ["validade_fim"])


def downgrade() -> None:
    op.drop_index("ix_certificado_validade_fim", table_name="certificado")
    op.drop_index("ix_certificado_empresa", table_name="certificado")
    op.drop_table("certificado")
    postgresql.ENUM(name="tipo_certificado").drop(op.get_bind(), checkfirst=True)
