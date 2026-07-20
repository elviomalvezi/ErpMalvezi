import uuid

import structlog

from app.core.exceptions import DomainError, NotFoundError
from app.modules.permissao.models import UsuarioPermissao
from app.modules.permissao.repository import PermissaoRepository
from app.modules.permissao.schemas import (
    ConcederPermissoesRequest,
    PermissaoMatrizItem,
    UsuarioPermissoesResponse,
)
from app.modules.usuario.repository import UsuarioRepository

logger = structlog.get_logger()


class PermissaoService:
    def __init__(self, repo: PermissaoRepository, usuario_repo: UsuarioRepository) -> None:
        self._repo = repo
        self._usuario_repo = usuario_repo

    async def listar_permissoes_usuario(
        self, usuario_id: uuid.UUID
    ) -> UsuarioPermissoesResponse:
        usuario = await self._usuario_repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        permissoes = await self._repo.listar_permissoes_usuario(usuario_id)
        return UsuarioPermissoesResponse(
            usuario_id=usuario_id,
            admin=usuario.admin,
            permissoes=permissoes,
        )

    async def conceder_permissoes(
        self,
        usuario_id: uuid.UUID,
        data: ConcederPermissoesRequest,
        concedido_por: uuid.UUID,
    ) -> list[PermissaoMatrizItem]:
        usuario = await self._usuario_repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        for item in data.permissoes:
            menu = await self._repo.get_menu_by_chave(item.menu_chave)
            if menu is None:
                raise DomainError(f"Menu '{item.menu_chave}' não encontrado.")
            acao = await self._repo.get_acao_by_chave(item.acao_chave)
            if acao is None:
                raise DomainError(f"Ação '{item.acao_chave}' não encontrada.")

            existente = await self._repo.get_permissao(usuario_id, menu.id, acao.id)
            if existente is not None:
                continue

            permissao = UsuarioPermissao(
                usuario_id=usuario_id,
                menu_id=menu.id,
                acao_id=acao.id,
                concedido_por=concedido_por,
            )
            await self._repo.conceder(permissao)
            logger.info(
                "permissao_concedida",
                usuario_id=str(usuario_id),
                menu=item.menu_chave,
                acao=item.acao_chave,
                concedido_por=str(concedido_por),
            )

        await self._repo.commit()
        return await self._repo.listar_permissoes_usuario(usuario_id)

    async def revogar_permissao(
        self, permissao_id: uuid.UUID, revogado_por: uuid.UUID
    ) -> None:
        permissao = await self._repo.get_permissao_by_id(permissao_id)
        if permissao is None:
            raise NotFoundError("Permissão não encontrada.")

        await self._repo.revogar(permissao)
        await self._repo.commit()
        logger.info(
            "permissao_revogada",
            permissao_id=str(permissao_id),
            revogado_por=str(revogado_por),
        )

    async def substituir_permissoes(
        self,
        usuario_id: uuid.UUID,
        data: ConcederPermissoesRequest,
        concedido_por: uuid.UUID,
    ) -> list[PermissaoMatrizItem]:
        usuario = await self._usuario_repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        await self._repo.revogar_todas_usuario(usuario_id)

        for item in data.permissoes:
            menu = await self._repo.get_menu_by_chave(item.menu_chave)
            if menu is None:
                raise DomainError(f"Menu '{item.menu_chave}' não encontrado.")
            acao = await self._repo.get_acao_by_chave(item.acao_chave)
            if acao is None:
                raise DomainError(f"Ação '{item.acao_chave}' não encontrada.")

            permissao = UsuarioPermissao(
                usuario_id=usuario_id,
                menu_id=menu.id,
                acao_id=acao.id,
                concedido_por=concedido_por,
            )
            await self._repo.conceder(permissao)

        await self._repo.commit()
        logger.info(
            "permissoes_substituidas",
            usuario_id=str(usuario_id),
            total=len(data.permissoes),
            concedido_por=str(concedido_por),
        )
        return await self._repo.listar_permissoes_usuario(usuario_id)
