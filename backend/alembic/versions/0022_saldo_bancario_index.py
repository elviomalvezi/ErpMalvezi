"""saldo_bancario_index

Revision ID: 0022
Revises: 0021
Create Date: 2026-06-12

Adiciona índice composto (conta_bancaria_id, status, data_vencimento) para
otimizar o cálculo de saldo bancário real (saldo_inicial + movimentações pagas).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_lancamento_saldo",
        "lancamento",
        ["conta_bancaria_id", "status", "data_vencimento"],
    )


def downgrade() -> None:
    op.drop_index("ix_lancamento_saldo", table_name="lancamento")
