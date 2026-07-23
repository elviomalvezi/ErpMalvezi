import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empresa.models import DominioSistema, Empresa, EmpresaDominio, UsuarioEmpresa


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

    async def get_by_codigo(self, codigo: str) -> Empresa | None:
        result = await self.db.execute(select(Empresa).where(Empresa.codigo == codigo))
        return result.scalar_one_or_none()

    async def proximo_codigo(self) -> str:
        """Próximo código sequencial de 3 dígitos ("001", "002", ...)."""
        result = await self.db.execute(select(Empresa.codigo))
        numericos = [
            int(c) for c in result.scalars().all() if c is not None and c.isdigit()
        ]
        return f"{(max(numericos) + 1) if numericos else 1:03d}"

    async def list_dominios(self, empresa_id: uuid.UUID) -> Sequence[EmpresaDominio]:
        result = await self.db.execute(
            select(EmpresaDominio)
            .where(EmpresaDominio.empresa_id == empresa_id)
            .order_by(EmpresaDominio.dominio)
        )
        return result.scalars().all()

    async def replace_dominios(
        self, empresa_id: uuid.UUID, dominios: list[DominioSistema]
    ) -> None:
        await self.db.execute(
            delete(EmpresaDominio).where(EmpresaDominio.empresa_id == empresa_id)
        )
        for dominio in dominios:
            self.db.add(
                EmpresaDominio(empresa_id=empresa_id, dominio=dominio, habilitado=True)
            )
        await self.db.flush()
