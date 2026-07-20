"""pessoa: corrige colisão do enum tipo (interno/externo)

A migration 0030 tentou criar o enum `tipo_pessoa`, mas já existia um com esse
nome (PJ/PF, usado por empresa/contato); com checkfirst a coluna `pessoa.tipo`
ficou apontando para o enum errado. Cria o enum correto `pessoa_tipo`
(interno/externo) e aponta a coluna para ele. Tabela vazia → alteração segura.

Revision ID: 0031
Revises: 0030
Create Date: 2026-06-29
"""

from __future__ import annotations

from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE pessoa_tipo AS ENUM ('interno', 'externo')")
    op.execute(
        "ALTER TABLE pessoa ALTER COLUMN tipo TYPE pessoa_tipo "
        "USING tipo::text::pessoa_tipo"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE pessoa ALTER COLUMN tipo TYPE tipo_pessoa "
        "USING tipo::text::tipo_pessoa"
    )
    op.execute("DROP TYPE pessoa_tipo")
