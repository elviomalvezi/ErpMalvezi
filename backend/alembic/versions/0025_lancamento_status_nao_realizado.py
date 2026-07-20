"""lancamento: status nao_realizado

Revision ID: 0025
Revises: 0024
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Novo valor do enum: previsto que comprovadamente não ocorreu.
    # PostgreSQL 12+ permite ADD VALUE dentro de transação (o valor só não
    # pode ser usado na mesma transação — aqui apenas o declaramos).
    op.execute("ALTER TYPE status_lancamento ADD VALUE IF NOT EXISTS 'nao_realizado'")


def downgrade() -> None:
    # PostgreSQL não suporta remover valores de um enum; downgrade é no-op.
    pass
