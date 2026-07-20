import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.empresa.models import UsuarioEmpresa


class ContaBancariaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(
            UsuarioEmpresa.usuario_id == usuario_id
        )

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        tipo: TipoConta | None = None,
        apenas_ativas: bool = True,
    ) -> list[ContaBancaria]:
        stmt = select(ContaBancaria).where(
            ContaBancaria.empresa_id.in_(self._sq_empresas(usuario_id))
        )
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

    async def tem_acesso(self, conta_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(ContaBancaria.id).where(
                ContaBancaria.id == conta_id,
                ContaBancaria.empresa_id.in_(self._sq_empresas(usuario_id)),
            )
        )
        return result.scalar_one_or_none() is not None

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

    async def get_by_dados_bancarios(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID,
        banco: str,
        agencia: str | None,
        numero_conta: str | None,
    ) -> ContaBancaria | None:
        stmt = select(ContaBancaria).where(
            ContaBancaria.empresa_id.in_(self._sq_empresas(usuario_id)),
            ContaBancaria.empresa_id == empresa_id,
            ContaBancaria.banco.ilike(banco),
            ContaBancaria.ativa.is_(True),
        )
        if agencia:
            stmt = stmt.where(ContaBancaria.agencia == agencia)
        if numero_conta:
            stmt = stmt.where(ContaBancaria.numero_conta == numero_conta)
        result = await self._db.execute(stmt.limit(1))
        return result.scalar_one_or_none()
