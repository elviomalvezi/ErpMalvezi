import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.conciliacao.models import (
    ImportacaoBancaria,
    RegraCategorizacao,
    StatusTransacao,
    TransacaoBancaria,
)
from app.modules.empresa.models import UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, TipoLancamento


class ConciliacaoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

    async def tem_acesso_empresa(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(UsuarioEmpresa.empresa_id).where(
                UsuarioEmpresa.usuario_id == usuario_id,
                UsuarioEmpresa.empresa_id == empresa_id,
            )
        )
        return result.scalar_one_or_none() is not None

    # --- ImportacaoBancaria ---

    async def create_importacao(self, importacao: ImportacaoBancaria) -> ImportacaoBancaria:
        self._db.add(importacao)
        await self._db.flush()
        return importacao

    async def get_importacao(self, importacao_id: uuid.UUID) -> ImportacaoBancaria | None:
        return await self._db.get(ImportacaoBancaria, importacao_id)

    async def listar_importacoes(
        self,
        usuario_id: uuid.UUID,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> list[ImportacaoBancaria]:
        stmt = (
            select(ImportacaoBancaria)
            .where(ImportacaoBancaria.empresa_id.in_(self._sq_empresas(usuario_id)))
            .order_by(ImportacaoBancaria.criado_em.desc())
        )
        if conta_bancaria_id is not None:
            stmt = stmt.where(ImportacaoBancaria.conta_bancaria_id == conta_bancaria_id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    # --- TransacaoBancaria ---

    async def create_transacoes(self, transacoes: list[TransacaoBancaria]) -> None:
        for t in transacoes:
            self._db.add(t)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def get_transacao(self, transacao_id: uuid.UUID) -> TransacaoBancaria | None:
        return await self._db.get(TransacaoBancaria, transacao_id)

    async def listar_transacoes(
        self,
        importacao_id: uuid.UUID,
        status: StatusTransacao | None = None,
    ) -> list[TransacaoBancaria]:
        stmt = (
            select(TransacaoBancaria)
            .where(TransacaoBancaria.importacao_id == importacao_id)
            .order_by(TransacaoBancaria.data)
        )
        if status is not None:
            stmt = stmt.where(TransacaoBancaria.status == status)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def id_externo_existe(self, conta_bancaria_id: uuid.UUID, id_externo: str) -> bool:
        stmt = select(TransacaoBancaria.id).where(
            TransacaoBancaria.conta_bancaria_id == conta_bancaria_id,
            TransacaoBancaria.id_externo == id_externo,
        )
        result = await self._db.execute(stmt)
        return result.scalar() is not None

    # --- Matching ---

    async def buscar_lancamentos_para_match(
        self,
        conta_bancaria_id: uuid.UUID,
        usuario_id: uuid.UUID,
        data: date,
        valor: Decimal,
        janela_dias: int = 3,
    ) -> list[Lancamento]:
        stmt = (
            select(Lancamento)
            .where(
                Lancamento.conta_bancaria_id == conta_bancaria_id,
                Lancamento.usuario_id == usuario_id,
                Lancamento.valor == valor,
                Lancamento.ativo.is_(True),
                Lancamento.data_vencimento >= data - timedelta(days=janela_dias),
                Lancamento.data_vencimento <= data + timedelta(days=janela_dias),
            )
            .order_by(Lancamento.data_vencimento)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    # --- RegraCategorizacao ---

    async def upsert_regra(
        self,
        usuario_id: uuid.UUID,
        padrao: str,
        categoria_id: uuid.UUID | None,
        tipo_lancamento: TipoLancamento | None,
        contato_id: uuid.UUID | None,
    ) -> None:
        stmt = (
            pg_insert(RegraCategorizacao)
            .values(
                usuario_id=usuario_id,
                padrao=padrao,
                categoria_id=categoria_id,
                tipo_lancamento=tipo_lancamento,
                contato_id=contato_id,
                contador=1,
                ativo=True,
            )
            .on_conflict_do_update(
                constraint="uq_regra_usuario_padrao",
                set_={
                    "contador": RegraCategorizacao.contador + 1,
                    "categoria_id": categoria_id,
                    "tipo_lancamento": tipo_lancamento,
                    "contato_id": contato_id,
                },
            )
        )
        await self._db.execute(stmt)

    async def buscar_regra(
        self, usuario_id: uuid.UUID, padrao: str
    ) -> RegraCategorizacao | None:
        stmt = (
            select(RegraCategorizacao)
            .where(
                RegraCategorizacao.usuario_id == usuario_id,
                RegraCategorizacao.ativo.is_(True),
            )
            .order_by(RegraCategorizacao.contador.desc())
        )
        result = await self._db.execute(stmt)
        regras = list(result.scalars().all())
        for regra in regras:
            if regra.padrao in padrao or padrao in regra.padrao:
                return regra
        return None
