"""modulo_auth

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-09

Cria as tabelas: token_seguranca, sessao, tentativa_login
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── token_seguranca ────────────────────────────────────────────────────
    op.create_table(
        "token_seguranca",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_token_seguranca_hash"),
    )
    op.create_index(
        "ix_token_seguranca_usuario_tipo", "token_seguranca", ["usuario_id", "tipo"]
    )

    # ── sessao ─────────────────────────────────────────────────────────────
    op.create_table(
        "sessao",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_jti", sa.String(36), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revogada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_origem", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_jti", name="uq_sessao_jti"),
    )
    op.create_index("ix_sessao_usuario_id", "sessao", ["usuario_id"])
    op.create_index("ix_sessao_token_jti", "sessao", ["token_jti"])

    # ── tentativa_login ────────────────────────────────────────────────────
    op.create_table(
        "tentativa_login",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("ip_origem", sa.String(45), nullable=True),
        sa.Column("sucesso", sa.Boolean(), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tentativa_login_email_criado_em", "tentativa_login", ["email", "criado_em"]
    )


def downgrade() -> None:
    op.drop_index("ix_tentativa_login_email_criado_em", table_name="tentativa_login")
    op.drop_table("tentativa_login")

    op.drop_index("ix_sessao_token_jti", table_name="sessao")
    op.drop_index("ix_sessao_usuario_id", table_name="sessao")
    op.drop_table("sessao")

    op.drop_index("ix_token_seguranca_usuario_tipo", table_name="token_seguranca")
    op.drop_table("token_seguranca")
