"""usuario: token_version para revogação de token

Adiciona token_version (default 0). Incrementar este valor invalida todos os
tokens JWT já emitidos para o usuário (logout forçado, inativação, troca de senha).

Revision ID: 0027
Revises: 0026
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("usuario", "token_version")
