"""tabela auditoria

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tabela", sa.String(100), nullable=False),
        sa.Column("registro_id", UUID(as_uuid=True), nullable=False),
        sa.Column("acao", sa.String(10), nullable=False),  # insert / update / delete
        sa.Column("usuario_id", UUID(as_uuid=True), nullable=True),
        sa.Column("valor_anterior", JSONB, nullable=True),
        sa.Column("valor_novo", JSONB, nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auditoria_tabela_registro", "auditoria", ["tabela", "registro_id"])
    op.create_index("ix_auditoria_usuario", "auditoria", ["usuario_id"])


def downgrade() -> None:
    op.drop_table("auditoria")
