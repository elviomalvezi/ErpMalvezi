import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.empresa.models import UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento, TipoLancamento


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

    async def kpi_lancamentos(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_id: uuid.UUID | None = None,
    ) -> list[dict]:
        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(
                Lancamento.tipo,
                Lancamento.status,
                func.sum(Lancamento.valor).label("total"),
            )
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.data_vencimento >= data_inicio,
                Lancamento.data_vencimento <= data_fim,
                Lancamento.status.in_(
                    [StatusLancamento.PENDENTE, StatusLancamento.PAGO]
                ),
            )
            .group_by(Lancamento.tipo, Lancamento.status)
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)

        result = await self._db.execute(stmt)
        return [
            {
                "tipo": r.tipo,
                "status": r.status,
                "total": Decimal(str(r.total or 0)),
            }
            for r in result.all()
        ]

    async def lancamentos_vencendo(
        self,
        usuario_id: uuid.UUID,
        data_ref: date,
        empresa_id: uuid.UUID | None = None,
        limite: int = 10,
    ) -> list[Lancamento]:
        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PENDENTE,
                Lancamento.data_vencimento == data_ref,
            )
            .order_by(Lancamento.data_vencimento, Lancamento.valor.desc())
            .limit(limite)
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def lancamentos_vencidos(
        self,
        usuario_id: uuid.UUID,
        data_ref: date,
        empresa_id: uuid.UUID | None = None,
        limite: int = 10,
    ) -> list[Lancamento]:
        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PENDENTE,
                Lancamento.data_vencimento < data_ref,
            )
            .order_by(Lancamento.data_vencimento)
            .limit(limite)
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def proximos_vencimentos(
        self,
        usuario_id: uuid.UUID,
        data_ref: date,
        empresa_id: uuid.UUID | None = None,
        dias: int = 7,
        limite: int = 10,
    ) -> list[Lancamento]:
        from datetime import timedelta

        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PENDENTE,
                Lancamento.data_vencimento > data_ref,
                Lancamento.data_vencimento <= data_ref + timedelta(days=dias),
            )
            .order_by(Lancamento.data_vencimento)
            .limit(limite)
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def despesas_por_categoria(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_id: uuid.UUID | None = None,
    ) -> list[dict]:
        from app.modules.categoria.models import Categoria

        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(
                Categoria.nome.label("categoria"),
                func.sum(Lancamento.valor).label("total"),
            )
            .join(Categoria, Categoria.id == Lancamento.categoria_id)
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PAGO,
                Lancamento.data_pagamento >= data_inicio,
                Lancamento.data_pagamento <= data_fim,
                Lancamento.tipo == "DESPESA",
            )
            .group_by(Categoria.nome)
            .order_by(func.sum(Lancamento.valor).desc())
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return [{"categoria": r.categoria, "total": Decimal(str(r.total or 0))} for r in result.all()]

    async def evolucao_mensal(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        meses: int = 6,
    ) -> list[dict]:
        from datetime import date as date_type
        from datetime import timedelta

        hoje = date_type.today()
        resultado = []
        for i in range(meses - 1, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            while mes <= 0:
                mes += 12
                ano -= 1
            inicio = date_type(ano, mes, 1)
            if mes == 12:
                fim = date_type(ano + 1, 1, 1) - timedelta(days=1)
            else:
                fim = date_type(ano, mes + 1, 1) - timedelta(days=1)
            rows = await self.kpi_lancamentos(usuario_id, inicio, fim, empresa_id)
            rec = sum(r["total"] for r in rows if r["tipo"] == "RECEITA")
            desp = sum(r["total"] for r in rows if r["tipo"] == "DESPESA")
            resultado.append({
                "mes": inicio.strftime("%b/%y"),
                "receitas": float(rec),
                "despesas": float(desp),
            })
        return resultado

    async def alertas_count(
        self,
        usuario_id: uuid.UUID,
        data_ref: date,
        empresa_id: uuid.UUID | None = None,
    ) -> int:
        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(func.count())
            .where(
                Lancamento.empresa_id.in_(sq),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PENDENTE,
                Lancamento.data_vencimento <= data_ref,
            )
        )
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    async def saldo_contas(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
    ) -> Decimal:
        from app.modules.conta_bancaria.models import ContaBancaria, TipoConta

        sq_emp = self._sq_empresas(usuario_id)

        # Soma das movimentações pagas por conta, a partir de data_saldo_inicial
        sq_mov = (
            select(
                Lancamento.conta_bancaria_id,
                func.coalesce(
                    func.sum(
                        case(
                            (Lancamento.tipo == TipoLancamento.RECEITA, Lancamento.valor_pago),
                            else_=-Lancamento.valor_pago,
                        )
                    ),
                    0,
                ).label("total"),
            )
            .join(ContaBancaria, ContaBancaria.id == Lancamento.conta_bancaria_id)
            .where(
                Lancamento.empresa_id.in_(sq_emp),
                Lancamento.status == StatusLancamento.PAGO,
                Lancamento.ativo.is_(True),
                or_(
                    ContaBancaria.data_saldo_inicial.is_(None),
                    Lancamento.data_vencimento >= ContaBancaria.data_saldo_inicial,
                ),
            )
            .group_by(Lancamento.conta_bancaria_id)
            .subquery()
        )

        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        ContaBancaria.saldo_inicial + func.coalesce(sq_mov.c.total, 0)
                    ),
                    0,
                )
            )
            .outerjoin(sq_mov, sq_mov.c.conta_bancaria_id == ContaBancaria.id)
            .where(
                ContaBancaria.empresa_id.in_(sq_emp),
                ContaBancaria.ativa.is_(True),
                ContaBancaria.tipo != TipoConta.CARTAO_CREDITO,
            )
        )
        if empresa_id is not None:
            stmt = stmt.where(ContaBancaria.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return Decimal(str(result.scalar() or 0))
