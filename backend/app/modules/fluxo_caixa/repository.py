import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lancamento.models import Lancamento, StatusLancamento


class FluxoCaixaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def agregar_por_mes(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_id: uuid.UUID | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Retorna agregações mensais de receitas e despesas realizadas e previstas."""

        periodo_col = func.date_trunc("month", Lancamento.data_vencimento).label("periodo")
        tipo_col = Lancamento.tipo
        status_col = Lancamento.status

        stmt = (
            select(
                periodo_col,
                tipo_col,
                status_col,
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
            .group_by(periodo_col, tipo_col, status_col)
            .order_by(periodo_col)
        )

        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        if conta_bancaria_id is not None:
            stmt = stmt.where(Lancamento.conta_bancaria_id == conta_bancaria_id)

        result = await self._db.execute(stmt)
        rows = result.all()

        return [
            {
                "periodo": r.periodo.date() if hasattr(r.periodo, "date") else r.periodo,
                "tipo": r.tipo,
                "status": r.status,
                "total": Decimal(str(r.total or 0)),
            }
            for r in rows
        ]

    async def saldo_conta(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> Decimal:
        """Soma de saldo_inicial de contas bancárias como ponto de partida."""
        from app.modules.conta_bancaria.models import ContaBancaria

        stmt = select(func.coalesce(func.sum(ContaBancaria.saldo_inicial), 0)).where(
            ContaBancaria.usuario_id == usuario_id,
            ContaBancaria.ativa.is_(True),
        )
        if empresa_id is not None:
            stmt = stmt.where(ContaBancaria.empresa_id == empresa_id)
        if conta_bancaria_id is not None:
            stmt = stmt.where(ContaBancaria.id == conta_bancaria_id)

        result = await self._db.execute(stmt)
        return Decimal(str(result.scalar() or 0))
