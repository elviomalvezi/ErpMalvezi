"""lancamento_anexos

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-10

Cria tabela lancamento_anexo para armazenar arquivos anexados a lançamentos.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lancamento_anexo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lancamento_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lancamento.id", ondelete="CASCADE"),
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
    op.create_index("ix_lancamento_anexo_lancamento", "lancamento_anexo", ["lancamento_id"])


def downgrade() -> None:
    op.drop_index("ix_lancamento_anexo_lancamento", "lancamento_anexo")
    op.drop_table("lancamento_anexo")
