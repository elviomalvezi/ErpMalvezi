import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.contato.models import Contato


class ContatoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        eh_cliente: bool | None = None,
        eh_fornecedor: bool | None = None,
        apenas_ativas: bool = True,
    ) -> list[Contato]:
        stmt = select(Contato).where(Contato.usuario_id == usuario_id)
        if apenas_ativas:
            stmt = stmt.where(Contato.ativa.is_(True))
        if empresa_id is not None:
            stmt = stmt.where(
                (Contato.empresa_id == empresa_id) | (Contato.escopo == "global")
            )
        if eh_cliente is not None:
            stmt = stmt.where(Contato.eh_cliente.is_(eh_cliente))
        if eh_fornecedor is not None:
            stmt = stmt.where(Contato.eh_fornecedor.is_(eh_fornecedor))
        stmt = stmt.order_by(Contato.nome_principal)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_nome(self, nome: str, usuario_id: uuid.UUID) -> Contato | None:
        result = await self._db.execute(
            select(Contato).where(
                Contato.usuario_id == usuario_id,
                Contato.nome_principal.ilike(nome),
                Contato.ativa.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, contato_id: uuid.UUID) -> Contato | None:
        return await self._db.get(Contato, contato_id)

    async def create(self, contato: Contato) -> None:
        self._db.add(contato)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Contato) -> None:
        await self._db.refresh(obj)

    async def ja_existe_documento(
        self,
        usuario_id: uuid.UUID,
        documento: str,
        excluir_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = select(Contato.id).where(
            Contato.usuario_id == usuario_id,
            Contato.documento == documento,
        )
        if excluir_id is not None:
            stmt = stmt.where(Contato.id != excluir_id)
        result = await self._db.execute(stmt)
        return result.first() is not None

    async def has_lancamentos(self, contato_id: uuid.UUID) -> bool:
        # stub — implementar quando o módulo lancamento existir
        return False
