import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fatura.models import Fatura, StatusFatura


class FaturaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        conta_bancaria_id: uuid.UUID | None = None,
        empresa_id: uuid.UUID | None = None,
        status: StatusFatura | None = None,
        competencia_inicio: date | None = None,
        competencia_fim: date | None = None,
    ) -> list[Fatura]:
        stmt = select(Fatura).where(Fatura.usuario_id == usuario_id)
        if conta_bancaria_id is not None:
            stmt = stmt.where(Fatura.conta_bancaria_id == conta_bancaria_id)
        if empresa_id is not None:
            stmt = stmt.where(Fatura.empresa_id == empresa_id)
        if status is not None:
            stmt = stmt.where(Fatura.status == status)
        if competencia_inicio is not None:
            stmt = stmt.where(Fatura.competencia >= competencia_inicio)
        if competencia_fim is not None:
            stmt = stmt.where(Fatura.competencia <= competencia_fim)
        stmt = stmt.order_by(Fatura.competencia.desc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, fatura_id: uuid.UUID) -> Fatura | None:
        return await self._db.get(Fatura, fatura_id)

    async def get_by_conta_competencia(
        self, conta_bancaria_id: uuid.UUID, competencia: date
    ) -> Fatura | None:
        stmt = select(Fatura).where(
            Fatura.conta_bancaria_id == conta_bancaria_id,
            Fatura.competencia == competencia,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, fatura: Fatura) -> None:
        self._db.add(fatura)
        await self._db.flush()

    async def delta_valor_total(self, fatura_id: uuid.UUID, delta: Decimal) -> None:
        """Incrementa (ou decrementa se negativo) o valor_total atomicamente."""
        await self._db.execute(
            update(Fatura)
            .where(Fatura.id == fatura_id)
            .values(valor_total=Fatura.valor_total + delta)
        )
