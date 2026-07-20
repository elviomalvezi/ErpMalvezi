"""lancamento_indexes_perf

Revision ID: 0020
Revises: 0019
Create Date: 2026-06-06

Adiciona índices compostos na tabela lancamento para melhorar performance do fluxo de caixa,
dashboard e listagens filtradas por usuario_id.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice principal para consultas do fluxo de caixa sem filtro de empresa
    # (usuario_id, data_vencimento) cobre o WHERE mais comum:
    # WHERE usuario_id = ? AND ativo = true AND data_vencimento BETWEEN ? AND ?
    op.create_index(
        "ix_lancamento_usuario_vencimento",
        "lancamento",
        ["usuario_id", "data_vencimento"],
    )

    # Índice para consultas com filtro de empresa + usuário (tela de lançamentos filtrada)
    op.create_index(
        "ix_lancamento_usuario_empresa_vencimento",
        "lancamento",
        ["usuario_id", "empresa_id", "data_vencimento"],
    )

    # Índice para filtros por conta bancária (conciliação, fluxo filtrado por conta)
    op.create_index(
        "ix_lancamento_conta_vencimento",
        "lancamento",
        ["conta_bancaria_id", "data_vencimento"],
    )


def downgrade() -> None:
    op.drop_index("ix_lancamento_conta_vencimento", table_name="lancamento")
    op.drop_index("ix_lancamento_usuario_empresa_vencimento", table_name="lancamento")
    op.drop_index("ix_lancamento_usuario_vencimento", table_name="lancamento")
