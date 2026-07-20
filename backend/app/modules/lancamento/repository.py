import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.empresa.models import UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento, TipoLancamento


class LancamentoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

    async def tem_acesso(self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Lancamento.id).where(
                Lancamento.id == lancamento_id,
                Lancamento.empresa_id.in_(self._sq_empresas(usuario_id)),
            )
        )
        return result.scalar_one_or_none() is not None

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
        descricao: str | None = None,
        limit: int | None = None,
    ) -> list[Lancamento]:
        stmt = select(Lancamento).where(Lancamento.empresa_id.in_(self._sq_empresas(usuario_id)))
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
        if descricao is not None:
            stmt = stmt.where(Lancamento.descricao.ilike(f"%{descricao}%"))
        stmt = stmt.order_by(Lancamento.data_vencimento.desc(), Lancamento.numero_parcela)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def saldo_anterior(
        self,
        conta_bancaria_id: uuid.UUID,
        usuario_id: uuid.UUID,
        ate: date | None,
        saldo_inicial: Decimal = Decimal("0"),
        data_saldo_inicial: date | None = None,
    ) -> Decimal:
        sq = self._sq_empresas(usuario_id)
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (Lancamento.tipo == TipoLancamento.RECEITA, Lancamento.valor_pago),
                        else_=-Lancamento.valor_pago,
                    )
                ),
                0,
            )
        ).where(
            Lancamento.empresa_id.in_(sq),
            Lancamento.conta_bancaria_id == conta_bancaria_id,
            Lancamento.status == StatusLancamento.PAGO,
            Lancamento.ativo.is_(True),
        )
        if data_saldo_inicial is not None:
            stmt = stmt.where(Lancamento.data_vencimento >= data_saldo_inicial)
        if ate is not None:
            stmt = stmt.where(Lancamento.data_vencimento < ate)
        result = await self._db.execute(stmt)
        val = result.scalar()
        movimentos = Decimal(str(val)) if val is not None else Decimal("0")
        return saldo_inicial + movimentos

    async def listar_extrato(
        self,
        conta_bancaria_id: uuid.UUID,
        usuario_id: uuid.UUID,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> list[Lancamento]:
        sq = self._sq_empresas(usuario_id)
        stmt = select(Lancamento).where(
            Lancamento.empresa_id.in_(sq),
            Lancamento.conta_bancaria_id == conta_bancaria_id,
            Lancamento.ativo.is_(True),
        )
        if data_inicio is not None:
            stmt = stmt.where(Lancamento.data_vencimento >= data_inicio)
        if data_fim is not None:
            stmt = stmt.where(Lancamento.data_vencimento <= data_fim)
        stmt = stmt.order_by(
            func.coalesce(Lancamento.data_pagamento, Lancamento.data_vencimento).asc(),
            Lancamento.criado_em.asc(),
        )
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
