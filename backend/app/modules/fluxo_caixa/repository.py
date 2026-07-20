import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.empresa.models import UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento


class FluxoCaixaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

    async def agregar_por_mes(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_ids: list[uuid.UUID] | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> list[dict]:
        periodo_col = func.date_trunc("month", Lancamento.data_vencimento).label("periodo")

        sq = self._sq_empresas(usuario_id)
        stmt = (
            select(
                periodo_col,
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
            .group_by(periodo_col, Lancamento.tipo, Lancamento.status)
            .order_by(periodo_col)
        )

        if empresa_ids:
            stmt = stmt.where(Lancamento.empresa_id.in_(empresa_ids))
        if conta_bancaria_id is not None:
            stmt = stmt.where(Lancamento.conta_bancaria_id == conta_bancaria_id)

        result = await self._db.execute(stmt)
        return [
            {
                "periodo": r.periodo.date() if hasattr(r.periodo, "date") else r.periodo,
                "tipo": r.tipo,
                "status": r.status,
                "total": Decimal(str(r.total or 0)),
            }
            for r in result.all()
        ]

    async def saldo_conta(
        self,
        usuario_id: uuid.UUID,
        empresa_ids: list[uuid.UUID] | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> Decimal:
        from app.modules.conta_bancaria.models import ContaBancaria

        sq = self._sq_empresas(usuario_id)
        stmt = select(func.coalesce(func.sum(ContaBancaria.saldo_inicial), 0)).where(
            ContaBancaria.empresa_id.in_(sq),
            ContaBancaria.ativa.is_(True),
        )
        if empresa_ids:
            stmt = stmt.where(ContaBancaria.empresa_id.in_(empresa_ids))
        if conta_bancaria_id is not None:
            stmt = stmt.where(ContaBancaria.id == conta_bancaria_id)

        result = await self._db.execute(stmt)
        return Decimal(str(result.scalar() or 0))
