import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.categoria.models import Categoria
from app.modules.empresa.models import Empresa, UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento, TipoLancamento


class RelatorioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

    async def dre_por_categoria(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        tipo: TipoLancamento,
        empresa_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Soma de lançamentos pagos (regime de caixa) agrupados por categoria.

        Inclui todas as categorias acessíveis ao usuário (do tipo informado),
        mesmo sem lançamentos no período — total 0 nesse caso.
        """
        sq_emp = self._sq_empresas(usuario_id)

        # Escopo de empresa dos lançamentos somados. Sempre restrito às empresas
        # do usuário; se uma empresa específica foi informada, restringe a ela.
        emp_cond = Lancamento.empresa_id.in_(sq_emp)
        if empresa_id is not None:
            emp_cond = and_(emp_cond, Lancamento.empresa_id == empresa_id)

        soma_pago = func.coalesce(
            func.sum(
                case(
                    (
                        (Lancamento.status == StatusLancamento.PAGO)
                        & (Lancamento.ativo.is_(True))
                        & emp_cond
                        & (Lancamento.data_pagamento >= data_inicio)
                        & (Lancamento.data_pagamento <= data_fim),
                        Lancamento.valor_pago,
                    ),
                    else_=None,
                )
            ),
            0,
        ).label("total")

        stmt = (
            select(
                Categoria.id.label("categoria_id"),
                Categoria.nome.label("categoria_nome"),
                Categoria.nivel.label("nivel"),
                Categoria.parent_id.label("parent_id"),
                soma_pago,
            )
            .join(Lancamento, Lancamento.categoria_id == Categoria.id, isouter=True)
            .where(
                Categoria.ativa.is_(True),
                Categoria.tipo == tipo.value,
                # Categorias acessíveis: específicas das empresas do usuário + globais.
                or_(Categoria.empresa_id.in_(sq_emp), Categoria.empresa_id.is_(None)),
            )
            .group_by(Categoria.id, Categoria.nome, Categoria.nivel, Categoria.parent_id)
            .order_by(Categoria.nivel, Categoria.nome)
        )

        result = await self._db.execute(stmt)
        rows = []
        for r in result.all():
            rows.append(
                {
                    "categoria_id": str(r.categoria_id),
                    "categoria_nome": r.categoria_nome,
                    "nivel": r.nivel,
                    "parent_id": str(r.parent_id) if r.parent_id else None,
                    "total": Decimal(str(r.total or 0)),
                }
            )
        return rows

    async def nome_empresa(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> str | None:
        # Restrito às empresas do usuário (não vaza nome de empresa de terceiros).
        result = await self._db.execute(
            select(Empresa.nome_principal, Empresa.nome_alternativo).where(
                Empresa.id == empresa_id,
                Empresa.id.in_(self._sq_empresas(usuario_id)),
            )
        )
        row = result.first()
        if row is None:
            return None
        return row.nome_alternativo or row.nome_principal
