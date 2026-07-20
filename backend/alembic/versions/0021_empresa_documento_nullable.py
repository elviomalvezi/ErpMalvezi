"""empresa_documento_nullable

Revision ID: 0021
Revises: 0020
Create Date: 2026-06-06

Torna empresa.documento nullable para permitir criação de empresas durante
importação sem documento (CPF/CNPJ) disponível. A unicidade é preservada via
índice parcial (somente linhas com documento preenchido).
"""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove a constraint unique padrão (coluna) e o NOT NULL
    op.drop_index("ix_empresa_documento", table_name="empresa", if_exists=True)
    op.execute("ALTER TABLE empresa ALTER COLUMN documento DROP NOT NULL")
    # Índice parcial: unique somente onde documento IS NOT NULL
    op.execute(
        "CREATE UNIQUE INDEX ix_empresa_documento_not_null "
        "ON empresa(documento) WHERE documento IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_empresa_documento_not_null")
    op.execute("ALTER TABLE empresa ALTER COLUMN documento SET NOT NULL")
    op.create_index("ix_empresa_documento", "empresa", ["documento"], unique=True)
