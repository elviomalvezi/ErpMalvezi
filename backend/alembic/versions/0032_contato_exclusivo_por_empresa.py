"""contato: torna clientes/fornecedores exclusivos por empresa

- Troca a unique (usuario_id, documento) por (usuario_id, empresa_id, documento):
  o mesmo CNPJ pode existir em empresas diferentes, mas não duplicado na mesma.
- Migra a base: contatos 'global' usados por 1 empresa viram 'especifico' dela;
  usados por N empresas ganham uma cópia por empresa (a 1ª reaproveita o original)
  e os lançamentos de cada empresa passam a apontar para a cópia dela.
- Contatos globais sem nenhum lançamento permanecem globais (não há como inferir).

Revision ID: 0032
Revises: 0031
Create Date: 2026-07-09
"""

from __future__ import annotations

from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Remove a unique antiga ANTES de duplicar (senão cópias com mesmo
    #    documento colidiriam).
    op.drop_constraint("uq_contato_usuario_documento", "contato", type_="unique")

    # 2) Migração dos dados.
    op.execute(
        """
        DO $$
        DECLARE
            r RECORD;
            novo_id uuid;
        BEGIN
            FOR r IN
                SELECT contato_id, empresa_id, rn FROM (
                    SELECT c.id AS contato_id,
                           l.empresa_id,
                           row_number() OVER (PARTITION BY c.id ORDER BY l.empresa_id) AS rn
                    FROM contato c
                    JOIN (
                        SELECT DISTINCT contato_id, empresa_id
                        FROM lancamento
                        WHERE contato_id IS NOT NULL
                    ) l ON l.contato_id = c.id
                    WHERE c.escopo = 'global'
                ) t
                ORDER BY contato_id, rn
            LOOP
                IF r.rn = 1 THEN
                    -- Primeira empresa: o próprio contato passa a ser dela.
                    UPDATE contato
                       SET escopo = 'especifico',
                           empresa_id = r.empresa_id,
                           atualizado_em = now()
                     WHERE id = r.contato_id;
                ELSE
                    -- Demais empresas: cópia dedicada + lançamentos repontados.
                    novo_id := gen_random_uuid();
                    INSERT INTO contato (
                        id, usuario_id, empresa_id, tipo, documento, nome_principal,
                        nome_alternativo, eh_cliente, eh_fornecedor, escopo, email,
                        telefone, celular, site, cep, logradouro, numero, complemento,
                        bairro, cidade, uf, pais, observacoes, ativa, criado_em, atualizado_em
                    )
                    SELECT novo_id, usuario_id, r.empresa_id, tipo, documento, nome_principal,
                           nome_alternativo, eh_cliente, eh_fornecedor, 'especifico', email,
                           telefone, celular, site, cep, logradouro, numero, complemento,
                           bairro, cidade, uf, pais, observacoes, ativa, now(), now()
                      FROM contato
                     WHERE id = r.contato_id;

                    UPDATE lancamento
                       SET contato_id = novo_id
                     WHERE contato_id = r.contato_id
                       AND empresa_id = r.empresa_id;
                END IF;
            END LOOP;
        END $$;
        """
    )

    # 3) Cria a nova unique (valida o resultado da migração).
    op.create_unique_constraint(
        "uq_contato_usuario_empresa_documento",
        "contato",
        ["usuario_id", "empresa_id", "documento"],
    )


def downgrade() -> None:
    # Não é possível desfazer a duplicação com segurança (lançamentos repontados).
    # Restaura apenas a constraint original.
    op.drop_constraint("uq_contato_usuario_empresa_documento", "contato", type_="unique")
    op.create_unique_constraint(
        "uq_contato_usuario_documento", "contato", ["usuario_id", "documento"]
    )
