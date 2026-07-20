"""lancamento_anexo: conteudo BYTEA e caminho opcional

Armazena o conteúdo do anexo no próprio banco (BYTEA) para persistência e
backup consistente via pg_dump. `caminho` passa a ser opcional (legado).

Revision ID: 0026
Revises: 0025
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lancamento_anexo",
        sa.Column("conteudo", sa.LargeBinary(), nullable=True),
    )
    op.alter_column(
        "lancamento_anexo",
        "caminho",
        existing_type=sa.String(length=500),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "lancamento_anexo",
        "caminho",
        existing_type=sa.String(length=500),
        nullable=False,
    )
    op.drop_column("lancamento_anexo", "conteudo")
