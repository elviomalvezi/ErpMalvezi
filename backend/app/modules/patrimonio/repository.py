import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patrimonio.models import Imovel, StatusImovel, StatusVeiculo, Veiculo


class VeiculoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        status: StatusVeiculo | None = None,
        apenas_ativos: bool = True,
    ) -> list[Veiculo]:
        stmt = select(Veiculo).where(Veiculo.usuario_id == usuario_id)
        if apenas_ativos:
            stmt = stmt.where(Veiculo.ativo.is_(True))
        if empresa_id:
            stmt = stmt.where(Veiculo.empresa_id == empresa_id)
        if status:
            stmt = stmt.where(Veiculo.status == status)
        stmt = stmt.order_by(Veiculo.marca, Veiculo.modelo)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, veiculo_id: uuid.UUID) -> Veiculo | None:
        return await self._db.get(Veiculo, veiculo_id)

    async def create(self, veiculo: Veiculo) -> None:
        self._db.add(veiculo)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Veiculo) -> None:
        await self._db.refresh(obj)


class ImovelRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        status: StatusImovel | None = None,
        apenas_ativos: bool = True,
    ) -> list[Imovel]:
        stmt = select(Imovel).where(Imovel.usuario_id == usuario_id)
        if apenas_ativos:
            stmt = stmt.where(Imovel.ativo.is_(True))
        if empresa_id:
            stmt = stmt.where(Imovel.empresa_id == empresa_id)
        if status:
            stmt = stmt.where(Imovel.status == status)
        stmt = stmt.order_by(Imovel.descricao)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, imovel_id: uuid.UUID) -> Imovel | None:
        return await self._db.get(Imovel, imovel_id)

    async def create(self, imovel: Imovel) -> None:
        self._db.add(imovel)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Imovel) -> None:
        await self._db.refresh(obj)
