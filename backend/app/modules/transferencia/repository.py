import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transferencia.models import StatusTransferencia, Transferencia


class TransferenciaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        conta_id: uuid.UUID | None = None,
        status: StatusTransferencia | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        apenas_ativas: bool = True,
    ) -> list[Transferencia]:
        stmt = select(Transferencia).where(Transferencia.usuario_id == usuario_id)
        if apenas_ativas:
            stmt = stmt.where(Transferencia.ativo.is_(True))
        if empresa_id is not None:
            stmt = stmt.where(
                (Transferencia.empresa_origem_id == empresa_id)
                | (Transferencia.empresa_destino_id == empresa_id)
            )
        if conta_id is not None:
            stmt = stmt.where(
                (Transferencia.conta_origem_id == conta_id)
                | (Transferencia.conta_destino_id == conta_id)
            )
        if status is not None:
            stmt = stmt.where(Transferencia.status == status)
        if data_inicio is not None:
            stmt = stmt.where(Transferencia.data_transferencia >= data_inicio)
        if data_fim is not None:
            stmt = stmt.where(Transferencia.data_transferencia <= data_fim)
        stmt = stmt.order_by(Transferencia.data_transferencia.desc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, transferencia_id: uuid.UUID) -> Transferencia | None:
        return await self._db.get(Transferencia, transferencia_id)

    async def create(self, transferencia: Transferencia) -> None:
        self._db.add(transferencia)
        await self._db.flush()
