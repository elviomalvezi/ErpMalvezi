"""auditoria: adiciona atualizado_em ausente

O modelo Auditoria herda de BaseModel (criado_em + atualizado_em), mas a
migration 0018 criou a tabela apenas com criado_em — qualquer INSERT via ORM
falhava com UndefinedColumnError.

Revision ID: 0034
Revises: 0033
Create Date: 2026-07-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "auditoria",
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("auditoria", "atualizado_em")
