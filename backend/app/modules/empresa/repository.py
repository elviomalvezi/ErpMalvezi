import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empresa.models import Empresa, UsuarioEmpresa


class EmpresaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, empresa_id: uuid.UUID) -> Empresa | None:
        result = await self.db.execute(
            select(Empresa).where(Empresa.id == empresa_id)
        )
        return result.scalar_one_or_none()

    async def get_by_documento(self, documento: str) -> Empresa | None:
        result = await self.db.execute(
            select(Empresa).where(Empresa.documento == documento)
        )
        return result.scalar_one_or_none()

    async def get_by_nome(self, nome: str, usuario_id: uuid.UUID) -> Empresa | None:
        # Tenta match exato (case-insensitive) primeiro, depois parcial
        for pattern in (nome, f"%{nome}%"):
            result = await self.db.execute(
                select(Empresa)
                .join(UsuarioEmpresa, UsuarioEmpresa.empresa_id == Empresa.id)
                .where(
                    UsuarioEmpresa.usuario_id == usuario_id,
                    Empresa.nome_principal.ilike(pattern),
                )
                .limit(1)
            )
            empresa = result.scalar_one_or_none()
            if empresa is not None:
                return empresa
        return None

    async def list_by_usuario(self, usuario_id: uuid.UUID) -> Sequence[Empresa]:
        result = await self.db.execute(
            select(Empresa)
            .join(UsuarioEmpresa, UsuarioEmpresa.empresa_id == Empresa.id)
            .where(UsuarioEmpresa.usuario_id == usuario_id)
            .order_by(Empresa.nome_principal)
        )
        return result.scalars().all()

    async def create(self, empresa: Empresa) -> Empresa:
        self.db.add(empresa)
        await self.db.flush()
        await self.db.refresh(empresa)
        return empresa

    async def create_vinculo(self, vinculo: UsuarioEmpresa) -> UsuarioEmpresa:
        self.db.add(vinculo)
        await self.db.flush()
        return vinculo

    async def has_lancamentos(self, empresa_id: uuid.UUID) -> bool:
        """Verifica se a empresa possui lançamentos (impede exclusão definitiva)."""
        from sqlalchemy import func

        from app.modules.lancamento.models import Lancamento

        result = await self.db.execute(
            select(func.count()).select_from(Lancamento).where(Lancamento.empresa_id == empresa_id)
        )
        return (result.scalar() or 0) > 0

    async def get_vinculo(
        self, usuario_id: uuid.UUID, empresa_id: uuid.UUID
    ) -> UsuarioEmpresa | None:
        result = await self.db.execute(
            select(UsuarioEmpresa).where(
                UsuarioEmpresa.usuario_id == usuario_id,
                UsuarioEmpresa.empresa_id == empresa_id,
            )
        )
        return result.scalar_one_or_none()
