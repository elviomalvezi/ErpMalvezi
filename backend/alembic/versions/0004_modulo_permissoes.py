"""modulo_permissoes

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-09

Adiciona campo admin ao usuario.
Cria tabelas: menu, acao, usuario_permissao.
Insere seed de menus e ações.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── campo admin em usuario ─────────────────────────────────────────────
    op.add_column(
        "usuario",
        sa.Column("admin", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── menu ───────────────────────────────────────────────────────────────
    op.create_table(
        "menu",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chave", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("ordem", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.UniqueConstraint("chave", name="uq_menu_chave"),
    )

    # ── acao ───────────────────────────────────────────────────────────────
    op.create_table(
        "acao",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chave", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
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
        sa.UniqueConstraint("chave", name="uq_acao_chave"),
    )

    # ── usuario_permissao ──────────────────────────────────────────────────
    op.create_table(
        "usuario_permissao",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "menu_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("menu.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "acao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("acao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concedido_por",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.UniqueConstraint(
            "usuario_id", "menu_id", "acao_id", name="uq_usuario_permissao"
        ),
    )
    op.create_index(
        "ix_usuario_permissao_usuario", "usuario_permissao", ["usuario_id"]
    )

    # ── seed: menus ────────────────────────────────────────────────────────
    op.execute("""
        INSERT INTO menu (id, chave, nome, ordem) VALUES
        (gen_random_uuid(), 'multi_empresa',              'Multi-empresa',              1),
        (gen_random_uuid(), 'usuarios',                   'Usuários',                   2),
        (gen_random_uuid(), 'configuracoes_empresa',      'Configurações da Empresa',   3),
        (gen_random_uuid(), 'configuracoes_financeiras',  'Configurações Financeiras',  4),
        (gen_random_uuid(), 'categorias',                 'Categorias',                 5),
        (gen_random_uuid(), 'contatos',                   'Clientes e Fornecedores',    6),
        (gen_random_uuid(), 'contas_bancarias',           'Contas Bancárias',           7),
        (gen_random_uuid(), 'cartoes',                    'Cartões de Crédito',         8),
        (gen_random_uuid(), 'lancamentos',                'Lançamentos',                9),
        (gen_random_uuid(), 'transferencias',             'Transferências',            10),
        (gen_random_uuid(), 'conciliacao',                'Conciliação Bancária',      11),
        (gen_random_uuid(), 'fluxo_caixa',                'Fluxo de Caixa',            12),
        (gen_random_uuid(), 'dashboard',                  'Dashboard',                 13),
        (gen_random_uuid(), 'permissoes',                 'Gestão de Permissões',      14)
    """)

    # ── seed: ações ────────────────────────────────────────────────────────
    op.execute("""
        INSERT INTO acao (id, chave, nome) VALUES
        (gen_random_uuid(), 'visualizar',            'Visualizar'),
        (gen_random_uuid(), 'criar',                 'Criar'),
        (gen_random_uuid(), 'editar',                'Editar'),
        (gen_random_uuid(), 'excluir',               'Excluir / Inativar'),
        (gen_random_uuid(), 'exportar',              'Exportar'),
        (gen_random_uuid(), 'editar_apos_fechamento','Editar após Fechamento')
    """)


def downgrade() -> None:
    op.drop_index("ix_usuario_permissao_usuario", table_name="usuario_permissao")
    op.drop_table("usuario_permissao")
    op.drop_table("acao")
    op.drop_table("menu")
    op.drop_column("usuario", "admin")
