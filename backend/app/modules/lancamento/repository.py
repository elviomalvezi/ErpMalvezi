import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lancamento.models import Lancamento, StatusLancamento, TipoLancamento


class LancamentoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        tipo: TipoLancamento | None = None,
        status: StatusLancamento | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        categoria_id: uuid.UUID | None = None,
        contato_id: uuid.UUID | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
        grupo_parcelas_id: uuid.UUID | None = None,
        recorrencia_id: uuid.UUID | None = None,
        apenas_ativos: bool = True,
    ) -> list[Lancamento]:
        stmt = select(Lancamento).where(Lancamento.usuario_id == usuario_id)
        if apenas_ativos:
            stmt = stmt.where(Lancamento.ativo.is_(True))
        if empresa_id is not None:
            stmt = stmt.where(Lancamento.empresa_id == empresa_id)
        if tipo is not None:
            stmt = stmt.where(Lancamento.tipo == tipo)
        if status is not None:
            stmt = stmt.where(Lancamento.status == status)
        if data_inicio is not None:
            stmt = stmt.where(Lancamento.data_vencimento >= data_inicio)
        if data_fim is not None:
            stmt = stmt.where(Lancamento.data_vencimento <= data_fim)
        if categoria_id is not None:
            stmt = stmt.where(Lancamento.categoria_id == categoria_id)
        if contato_id is not None:
            stmt = stmt.where(Lancamento.contato_id == contato_id)
        if conta_bancaria_id is not None:
            stmt = stmt.where(Lancamento.conta_bancaria_id == conta_bancaria_id)
        if grupo_parcelas_id is not None:
            stmt = stmt.where(Lancamento.grupo_parcelas_id == grupo_parcelas_id)
        if recorrencia_id is not None:
            stmt = stmt.where(Lancamento.recorrencia_id == recorrencia_id)
        stmt = stmt.order_by(Lancamento.data_vencimento, Lancamento.numero_parcela)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, lancamento_id: uuid.UUID) -> Lancamento | None:
        return await self._db.get(Lancamento, lancamento_id)

    async def create(self, lancamento: Lancamento) -> None:
        self._db.add(lancamento)
        await self._db.flush()

    async def create_many(self, lancamentos: list[Lancamento]) -> None:
        for lct in lancamentos:
            self._db.add(lct)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Lancamento) -> None:
        await self._db.refresh(obj)
