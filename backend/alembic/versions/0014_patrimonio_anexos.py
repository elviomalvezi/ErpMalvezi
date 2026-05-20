"""patrimonio_anexos

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-11

Cria tabelas veiculo_anexo e imovel_anexo.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "veiculo_anexo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "veiculo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("veiculo.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("tamanho", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("caminho", sa.String(500), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_veiculo_anexo_veiculo", "veiculo_anexo", ["veiculo_id"])

    op.create_table(
        "imovel_anexo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "imovel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("imovel.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("tamanho", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("caminho", sa.String(500), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_imovel_anexo_imovel", "imovel_anexo", ["imovel_id"])


def downgrade() -> None:
    op.drop_index("ix_imovel_anexo_imovel", "imovel_anexo")
    op.drop_table("imovel_anexo")
    op.drop_index("ix_veiculo_anexo_veiculo", "veiculo_anexo")
    op.drop_table("veiculo_anexo")
