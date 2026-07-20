import uuid

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.certificado.models import Certificado
from app.modules.empresa.models import Empresa, UsuarioEmpresa
from app.modules.pessoa.models import Pessoa, PessoaCertificado


class PessoaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _certs_visiveis(self, usuario_id: uuid.UUID):
        sq = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)
        return or_(Certificado.empresa_id.in_(sq), Certificado.empresa_id.is_(None))

    async def listar(self, apenas_ativos: bool = True) -> list[Pessoa]:
        stmt: Select = select(Pessoa)
        if apenas_ativos:
            stmt = stmt.where(Pessoa.ativo.is_(True))
        stmt = stmt.order_by(Pessoa.nome)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, pessoa_id: uuid.UUID) -> Pessoa | None:
        return await self._db.get(Pessoa, pessoa_id)

    async def total_por_pessoa(self, pessoa_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not pessoa_ids:
            return {}
        result = await self._db.execute(
            select(PessoaCertificado.pessoa_id, func.count())
            .where(PessoaCertificado.pessoa_id.in_(pessoa_ids))
            .group_by(PessoaCertificado.pessoa_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def certificados_de_pessoa(self, pessoa_id: uuid.UUID) -> list[Certificado]:
        # Sem filtro de empresa: a associação é controle de entregas, visível a todos.
        result = await self._db.execute(
            select(Certificado)
            .join(PessoaCertificado, PessoaCertificado.certificado_id == Certificado.id)
            .where(PessoaCertificado.pessoa_id == pessoa_id)
            .order_by(Certificado.validade_fim.asc().nullslast(), Certificado.nome)
        )
        return list(result.scalars().all())

    async def cert_existe(self, certificado_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Certificado.id).where(Certificado.id == certificado_id)
        )
        return result.scalar_one_or_none() is not None

    async def empresas_nomes(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not ids:
            return {}
        result = await self._db.execute(
            select(Empresa.id, Empresa.nome_alternativo, Empresa.nome_principal).where(
                Empresa.id.in_(ids)
            )
        )
        return {r.id: (r.nome_alternativo or r.nome_principal) for r in result.all()}

    async def cert_ids_de_pessoa(self, pessoa_id: uuid.UUID) -> set[uuid.UUID]:
        result = await self._db.execute(
            select(PessoaCertificado.certificado_id).where(
                PessoaCertificado.pessoa_id == pessoa_id
            )
        )
        return set(result.scalars().all())

    async def pessoas_de_certificado(self, certificado_id: uuid.UUID) -> list[Pessoa]:
        result = await self._db.execute(
            select(Pessoa)
            .join(PessoaCertificado, PessoaCertificado.pessoa_id == Pessoa.id)
            .where(PessoaCertificado.certificado_id == certificado_id, Pessoa.ativo.is_(True))
            .order_by(Pessoa.nome)
        )
        return list(result.scalars().all())

    async def cert_acessivel(self, certificado_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Certificado.id).where(
                Certificado.id == certificado_id, self._certs_visiveis(usuario_id)
            )
        )
        return result.scalar_one_or_none() is not None

    async def assoc_existe(self, pessoa_id: uuid.UUID, certificado_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(PessoaCertificado.id).where(
                PessoaCertificado.pessoa_id == pessoa_id,
                PessoaCertificado.certificado_id == certificado_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def associar(self, pessoa_id: uuid.UUID, certificado_id: uuid.UUID) -> None:
        self._db.add(PessoaCertificado(pessoa_id=pessoa_id, certificado_id=certificado_id))
        await self._db.flush()

    async def desassociar(self, pessoa_id: uuid.UUID, certificado_id: uuid.UUID) -> None:
        await self._db.execute(
            delete(PessoaCertificado).where(
                PessoaCertificado.pessoa_id == pessoa_id,
                PessoaCertificado.certificado_id == certificado_id,
            )
        )

    async def remover_associacoes(self, pessoa_id: uuid.UUID, certificado_ids: list[uuid.UUID]) -> None:
        if not certificado_ids:
            return
        await self._db.execute(
            delete(PessoaCertificado).where(
                PessoaCertificado.pessoa_id == pessoa_id,
                PessoaCertificado.certificado_id.in_(certificado_ids),
            )
        )

    async def create(self, pessoa: Pessoa) -> None:
        self._db.add(pessoa)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Pessoa) -> None:
        await self._db.refresh(obj)
