import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lancamento.models import Lancamento, StatusLancamento


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def kpi_lancamentos(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_id: uuid.UUID | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                Lancamento.tipo,
                Lancamento.status,
                func.sum(Lancamento.valor).label("total"),
            )
            .where(
                Lancamento.usuario_id == usuario_id,
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
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.usuario_id == usuario_id,
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
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.usuario_id == usuario_id,
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

        stmt = (
            select(Lancamento)
            .where(
                Lancamento.usuario_id == usuario_id,
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

    async def saldo_contas(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
    ) -> Decimal:
        from app.modules.conta_bancaria.models import ContaBancaria

        stmt = select(func.coalesce(func.sum(ContaBancaria.saldo_inicial), 0)).where(
            ContaBancaria.usuario_id == usuario_id,
            ContaBancaria.ativa.is_(True),
        )
        if empresa_id is not None:
            stmt = stmt.where(ContaBancaria.empresa_id == empresa_id)
        result = await self._db.execute(stmt)
        return Decimal(str(result.scalar() or 0))
