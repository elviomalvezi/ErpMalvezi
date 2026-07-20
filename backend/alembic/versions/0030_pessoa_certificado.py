"""pessoa: cadastro de pessoas que possuem certificados (N:N)

Cria a tabela `pessoa` (interno/externo) e a associação `pessoa_certificado`
para registrar quem tem cada certificado instalado.

Revision ID: 0030
Revises: 0029
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_enum = postgresql.ENUM("interno", "externo", name="tipo_pessoa")
    tipo_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "pessoa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column(
            "tipo",
            postgresql.ENUM("interno", "externo", name="tipo_pessoa", create_type=False),
            nullable=False,
        ),
        sa.Column("setor", sa.String(150), nullable=True),
        sa.Column("empresa_externa", sa.String(200), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pessoa_certificado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "pessoa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pessoa.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "certificado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("certificado.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("pessoa_id", "certificado_id", name="uq_pessoa_certificado"),
    )
    op.create_index("ix_pessoa_certificado_pessoa", "pessoa_certificado", ["pessoa_id"])
    op.create_index("ix_pessoa_certificado_certificado", "pessoa_certificado", ["certificado_id"])

    # Adiciona a tela "Pessoas" na matriz de permissões.
    op.execute(
        """
        INSERT INTO menu (id, chave, nome, ordem) VALUES
        (gen_random_uuid(), 'pessoas', 'Pessoas dos Certificados', 21)
        ON CONFLICT (chave) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM menu WHERE chave = 'pessoas'")
    op.drop_index("ix_pessoa_certificado_certificado", table_name="pessoa_certificado")
    op.drop_index("ix_pessoa_certificado_pessoa", table_name="pessoa_certificado")
    op.drop_table("pessoa_certificado")
    op.drop_table("pessoa")
    # NÃO dropar 'tipo_pessoa' aqui: ele é o enum PJ/PF compartilhado (empresa/contato)
    # e nunca foi criado por esta migration. O enum próprio (pessoa_tipo) é tratado na 0031.
