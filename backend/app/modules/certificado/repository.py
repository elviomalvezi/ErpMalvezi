import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.certificado.models import Certificado, TipoCertificado
from app.modules.empresa.models import Empresa, UsuarioEmpresa


class CertificadoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(
            UsuarioEmpresa.usuario_id == usuario_id
        )

    def _visivel(self, usuario_id: uuid.UUID):
        # Vê certificados das empresas que acessa OU certificados globais (empresa nula).
        return or_(
            Certificado.empresa_id.in_(self._sq_empresas(usuario_id)),
            Certificado.empresa_id.is_(None),
        )

    async def listar(
        self,
        usuario_id: uuid.UUID,
        tipo: TipoCertificado | None = None,
        apenas_ativos: bool = True,
    ) -> list[Certificado]:
        stmt = select(Certificado).where(self._visivel(usuario_id))
        if apenas_ativos:
            stmt = stmt.where(Certificado.ativo.is_(True))
        if tipo is not None:
            stmt = stmt.where(Certificado.tipo == tipo)
        stmt = stmt.order_by(Certificado.validade_fim.asc().nullslast(), Certificado.nome)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, certificado_id: uuid.UUID) -> Certificado | None:
        return await self._db.get(Certificado, certificado_id)

    async def tem_acesso(self, certificado_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Certificado.id).where(
                Certificado.id == certificado_id,
                self._visivel(usuario_id),
            )
        )
        return result.scalar_one_or_none() is not None

    async def acesso_empresa(self, usuario_id: uuid.UUID, empresa_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(UsuarioEmpresa.empresa_id).where(
                UsuarioEmpresa.usuario_id == usuario_id,
                UsuarioEmpresa.empresa_id == empresa_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def empresa_por_documento(
        self, documento: str, usuario_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Acha a empresa (acessível ao usuário) cujo documento bate com `documento`
        (só dígitos). Usado para auto-vincular o certificado à empresa pelo CNPJ/CPF."""
        result = await self._db.execute(
            select(Empresa.id, Empresa.documento).where(
                Empresa.id.in_(self._sq_empresas(usuario_id))
            )
        )
        for row in result.all():
            if row.documento and "".join(c for c in row.documento if c.isdigit()) == documento:
                return row.id
        return None

    async def empresas_nomes(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not ids:
            return {}
        result = await self._db.execute(
            select(Empresa.id, Empresa.nome_alternativo, Empresa.nome_principal)
            .where(Empresa.id.in_(ids))
        )
        return {r.id: (r.nome_alternativo or r.nome_principal) for r in result.all()}

    async def get_arquivo(
        self, certificado_id: uuid.UUID
    ) -> tuple[bytes | None, str | None]:
        """Carrega o blob (coluna deferred) explicitamente — evita lazy-load,
        que não é permitido no SQLAlchemy async."""
        result = await self._db.execute(
            select(Certificado.arquivo, Certificado.arquivo_nome).where(
                Certificado.id == certificado_id
            )
        )
        row = result.one_or_none()
        if row is None:
            return None, None
        return row.arquivo, row.arquivo_nome

    async def create(self, certificado: Certificado) -> None:
        self._db.add(certificado)
        await self._db.flush()

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Certificado) -> None:
        await self._db.refresh(obj)
