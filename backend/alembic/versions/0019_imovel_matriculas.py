"""imovel matriculas multiplas

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "imovel_matricula",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("imovel_id", UUID(as_uuid=True), sa.ForeignKey("imovel.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero", sa.String(200), nullable=False),
        sa.Column("descricao", sa.String(300), nullable=True),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_imovel_matricula_imovel", "imovel_matricula", ["imovel_id"])

    # Migrar matrícula existente para a nova tabela como principal
    op.execute("""
        INSERT INTO imovel_matricula (id, imovel_id, numero, principal, criado_em, atualizado_em)
        SELECT gen_random_uuid(), id, matricula, true, NOW(), NOW()
        FROM imovel
        WHERE matricula IS NOT NULL AND matricula != ''
    """)


def downgrade() -> None:
    op.drop_table("imovel_matricula")
