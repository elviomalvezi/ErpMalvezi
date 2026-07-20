"""permissoes: adiciona telas faltantes na matriz de menus

Inclui na matriz usuário × tela × ação as telas que passaram a existir e não
estavam no seed original (0004): Certificados, Patrimonial, Inadimplência,
Extrato Bancário, Importação e DRE/Relatórios. Idempotente por `chave`.

Revision ID: 0029
Revises: 0028
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

_NOVOS_MENUS = [
    ("patrimonial", "Patrimonial (Imóveis e Veículos)", 15),
    ("certificados", "Certificados", 16),
    ("inadimplencia", "Inadimplência", 17),
    ("extrato_bancario", "Extrato Bancário", 18),
    ("importacao", "Importação em Lote", 19),
    ("relatorios", "DRE / Relatórios", 20),
]


def upgrade() -> None:
    valores = ",\n        ".join(
        f"(gen_random_uuid(), '{chave}', '{nome}', {ordem})"
        for chave, nome, ordem in _NOVOS_MENUS
    )
    op.execute(
        f"""
        INSERT INTO menu (id, chave, nome, ordem) VALUES
        {valores}
        ON CONFLICT (chave) DO NOTHING
        """
    )


def downgrade() -> None:
    chaves = ", ".join(f"'{chave}'" for chave, _, _ in _NOVOS_MENUS)
    op.execute(f"DELETE FROM menu WHERE chave IN ({chaves})")
