"""modulo_categorias

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-09

Cria a tabela: categoria (hierárquica, 3 níveis, global/específico)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categoria",
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
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("escopo", sa.String(12), nullable=False, server_default="global"),
        sa.Column("nivel", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("codigo", sa.String(20), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
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
    op.create_index("ix_categoria_usuario_tipo", "categoria", ["usuario_id", "tipo"])
    op.create_index("ix_categoria_empresa", "categoria", ["empresa_id"])
    op.create_index("ix_categoria_parent", "categoria", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_categoria_parent", table_name="categoria")
    op.drop_index("ix_categoria_empresa", table_name="categoria")
    op.drop_index("ix_categoria_usuario_tipo", table_name="categoria")
    op.drop_table("categoria")
