import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.permissao.models import Acao, Menu, UsuarioPermissao
from app.modules.permissao.schemas import PermissaoMatrizItem
from app.modules.usuario.models import Usuario


class PermissaoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def listar_menus(self) -> list[Menu]:
        result = await self._db.execute(
            select(Menu).where(Menu.ativo.is_(True)).order_by(Menu.ordem)
        )
        return list(result.scalars())

    async def listar_acoes(self) -> list[Acao]:
        result = await self._db.execute(select(Acao).order_by(Acao.chave))
        return list(result.scalars())

    async def get_menu_by_chave(self, chave: str) -> Menu | None:
        result = await self._db.execute(select(Menu).where(Menu.chave == chave))
        return result.scalar_one_or_none()

    async def get_acao_by_chave(self, chave: str) -> Acao | None:
        result = await self._db.execute(select(Acao).where(Acao.chave == chave))
        return result.scalar_one_or_none()

    async def get_permissao(
        self, usuario_id: uuid.UUID, menu_id: uuid.UUID, acao_id: uuid.UUID
    ) -> UsuarioPermissao | None:
        result = await self._db.execute(
            select(UsuarioPermissao).where(
                UsuarioPermissao.usuario_id == usuario_id,
                UsuarioPermissao.menu_id == menu_id,
                UsuarioPermissao.acao_id == acao_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_permissao_by_id(self, permissao_id: uuid.UUID) -> UsuarioPermissao | None:
        result = await self._db.execute(
            select(UsuarioPermissao).where(UsuarioPermissao.id == permissao_id)
        )
        return result.scalar_one_or_none()

    async def listar_permissoes_usuario(
        self, usuario_id: uuid.UUID
    ) -> list[PermissaoMatrizItem]:
        result = await self._db.execute(
            select(
                UsuarioPermissao.id,
                Menu.chave.label("menu_chave"),
                Menu.nome.label("menu_nome"),
                Acao.chave.label("acao_chave"),
                Acao.nome.label("acao_nome"),
            )
            .join(Menu, UsuarioPermissao.menu_id == Menu.id)
            .join(Acao, UsuarioPermissao.acao_id == Acao.id)
            .where(UsuarioPermissao.usuario_id == usuario_id)
            .order_by(Menu.ordem, Acao.chave)
        )
        rows = result.all()
        return [
            PermissaoMatrizItem(
                permissao_id=row.id,
                menu_chave=row.menu_chave,
                menu_nome=row.menu_nome,
                acao_chave=row.acao_chave,
                acao_nome=row.acao_nome,
            )
            for row in rows
        ]

    async def conceder(self, permissao: UsuarioPermissao) -> UsuarioPermissao:
        self._db.add(permissao)
        await self._db.flush()
        return permissao

    async def revogar(self, permissao: UsuarioPermissao) -> None:
        await self._db.delete(permissao)

    async def revogar_todas_usuario(self, usuario_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(UsuarioPermissao).where(UsuarioPermissao.usuario_id == usuario_id)
        )
        for p in result.scalars():
            await self._db.delete(p)

    async def verificar_permissao(
        self, usuario_id: uuid.UUID, menu_chave: str, acao_chave: str
    ) -> bool:
        result = await self._db.execute(
            select(Usuario.admin).where(Usuario.id == usuario_id)
        )
        admin = result.scalar_one_or_none()
        if admin:
            return True

        result = await self._db.execute(
            select(UsuarioPermissao.id)
            .join(Menu, UsuarioPermissao.menu_id == Menu.id)
            .join(Acao, UsuarioPermissao.acao_id == Acao.id)
            .where(
                UsuarioPermissao.usuario_id == usuario_id,
                Menu.chave == menu_chave,
                Acao.chave == acao_chave,
            )
        )
        return result.scalar_one_or_none() is not None
