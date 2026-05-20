import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conta_bancaria.models import ContaBancaria, TipoConta


class ContaBancariaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        tipo: TipoConta | None = None,
        apenas_ativas: bool = True,
    ) -> list[ContaBancaria]:
        stmt = select(ContaBancaria).where(ContaBancaria.usuario_id == usuario_id)
        if apenas_ativas:
            stmt = stmt.where(ContaBancaria.ativa.is_(True))
        if empresa_id is not None:
            stmt = stmt.where(ContaBancaria.empresa_id == empresa_id)
        if tipo is not None:
            stmt = stmt.where(ContaBancaria.tipo == tipo)
        stmt = stmt.order_by(ContaBancaria.nome)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, conta_id: uuid.UUID) -> ContaBancaria | None:
        return await self._db.get(ContaBancaria, conta_id)

    async def create(self, conta: ContaBancaria) -> None:
        self._db.add(conta)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: ContaBancaria) -> None:
        await self._db.refresh(obj)

    async def has_lancamentos(self, conta_id: uuid.UUID) -> bool:
        # stub — implementar quando o módulo lancamento existir
        return False
