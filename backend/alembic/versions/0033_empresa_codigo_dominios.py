"""empresa: código curto de seleção + domínios habilitáveis por empresa

- `empresa.codigo`: código curto único (ex.: "001") para seleção rápida na
  tela de entrada. Backfill sequencial por ordem de criação.
- `empresa_dominio`: quais domínios do ERP (financeiro, estoque, compras...)
  cada empresa tem habilitados. Empresas existentes iniciam com `financeiro`
  e `cadastros` habilitados (comportamento atual do sistema).

Revision ID: 0033
Revises: 0032
Create Date: 2026-07-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

_DOMINIOS = (
    "financeiro",
    "cadastros",
    "estoque",
    "compras",
    "vendas",
    "fiscal",
    "contabilidade",
    "servicos",
    "crm",
    "rh",
    "contratos",
    "ia",
    "producao",
)


def upgrade() -> None:
    # 1) Código curto da empresa, com backfill sequencial ("001", "002", ...).
    op.add_column("empresa", sa.Column("codigo", sa.String(10), nullable=True))
    op.execute(
        """
        UPDATE empresa
           SET codigo = t.novo
          FROM (
            SELECT id,
                   lpad((row_number() OVER (ORDER BY criado_em, id))::text, 3, '0') AS novo
              FROM empresa
          ) t
         WHERE empresa.id = t.id
        """
    )
    op.create_unique_constraint("uq_empresa_codigo", "empresa", ["codigo"])

    # 2) Enum e tabela de domínios habilitados.
    dominio_enum = postgresql.ENUM(*_DOMINIOS, name="dominio_sistema")
    dominio_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "empresa_dominio",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dominio",
            postgresql.ENUM(*_DOMINIOS, name="dominio_sistema", create_type=False),
            nullable=False,
        ),
        sa.Column("habilitado", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("empresa_id", "dominio", name="uq_empresa_dominio"),
    )
    op.create_index("ix_empresa_dominio_empresa", "empresa_dominio", ["empresa_id"])

    # 3) Empresas existentes: habilita os domínios já em operação hoje.
    op.execute(
        """
        INSERT INTO empresa_dominio (id, empresa_id, dominio, habilitado, criado_em, atualizado_em)
        SELECT gen_random_uuid(), e.id, d.dominio, true, now(), now()
          FROM empresa e
         CROSS JOIN (
            SELECT unnest(ARRAY['financeiro', 'cadastros']::dominio_sistema[]) AS dominio
         ) d
        """
    )


def downgrade() -> None:
    op.drop_index("ix_empresa_dominio_empresa", table_name="empresa_dominio")
    op.drop_table("empresa_dominio")
    op.execute("DROP TYPE IF EXISTS dominio_sistema")
    op.drop_constraint("uq_empresa_codigo", "empresa", type_="unique")
    op.drop_column("empresa", "codigo")
