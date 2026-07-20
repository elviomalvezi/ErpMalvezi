import uuid

from sqlalchemy import and_, case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.contato.models import Contato
from app.modules.empresa.models import UsuarioEmpresa


class ContatoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # --- helpers de acesso por empresa ----------------------------------------

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(
            UsuarioEmpresa.usuario_id == usuario_id
        )

    def _acesso_cond(self, usuario_id: uuid.UUID):
        """Membro de empresa acessa contatos dessa empresa + todos os globais."""
        sq_empresas = self._sq_empresas(usuario_id)
        return or_(
            Contato.empresa_id.in_(sq_empresas),
            Contato.empresa_id.is_(None),
        )

    # --------------------------------------------------------------------------

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        eh_cliente: bool | None = None,
        eh_fornecedor: bool | None = None,
        apenas_ativas: bool = True,
    ) -> list[Contato]:
        stmt = select(Contato).where(self._acesso_cond(usuario_id))
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

    async def tem_acesso(self, contato_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Contato.id).where(
                Contato.id == contato_id,
                self._acesso_cond(usuario_id),
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_nome(self, nome: str, usuario_id: uuid.UUID) -> Contato | None:
        result = await self._db.execute(
            select(Contato).where(
                self._acesso_cond(usuario_id),
                Contato.nome_principal.ilike(nome),
                Contato.ativa.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_nome_para_empresa(
        self, nome: str, usuario_id: uuid.UUID, empresa_id: uuid.UUID
    ) -> Contato | None:
        """Busca contato pelo nome no escopo de uma empresa.

        Prefere o contato específico da empresa; se não houver, aceita um global
        (compartilhado intencionalmente). Usado pela importação de lançamentos.
        """
        result = await self._db.execute(
            select(Contato)
            .where(
                self._acesso_cond(usuario_id),
                Contato.nome_principal.ilike(nome),
                Contato.ativa.is_(True),
                or_(
                    and_(Contato.escopo == "especifico", Contato.empresa_id == empresa_id),
                    Contato.escopo == "global",
                ),
            )
            .order_by(case((Contato.escopo == "especifico", 0), else_=1))
            .limit(1)
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
            self._acesso_cond(usuario_id),
            Contato.documento == documento,
        )
        if excluir_id is not None:
            stmt = stmt.where(Contato.id != excluir_id)
        result = await self._db.execute(stmt)
        return result.first() is not None

    async def has_lancamentos(self, contato_id: uuid.UUID) -> bool:
        # stub — implementar quando o módulo lancamento existir
        return False
