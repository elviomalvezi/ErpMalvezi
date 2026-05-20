import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import DomainError, NotFoundError
from app.modules.permissao.models import Acao, Menu, UsuarioPermissao
from app.modules.permissao.schemas import (
    ConcederPermissoesRequest,
    PermissaoItem,
    PermissaoMatrizItem,
)
from app.modules.permissao.service import PermissaoService
from app.modules.usuario.models import Usuario


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_usuario_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock, mock_usuario_repo: AsyncMock) -> PermissaoService:
    return PermissaoService(mock_repo, mock_usuario_repo)


def _make_usuario(admin: bool = False) -> MagicMock:
    u = MagicMock(spec=Usuario)
    u.id = uuid.uuid4()
    u.admin = admin
    return u


def _make_menu(chave: str = "lancamentos") -> MagicMock:
    m = MagicMock(spec=Menu)
    m.id = uuid.uuid4()
    m.chave = chave
    return m


def _make_acao(chave: str = "criar") -> MagicMock:
    a = MagicMock(spec=Acao)
    a.id = uuid.uuid4()
    a.chave = chave
    return a


class TestListarPermissoes:
    async def test_usuario_nao_encontrado(
        self, svc: PermissaoService, mock_usuario_repo: AsyncMock
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.listar_permissoes_usuario(uuid.uuid4())

    async def test_retorna_resposta_com_admin_flag(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        usuario = _make_usuario(admin=True)
        mock_usuario_repo.get_by_id.return_value = usuario
        mock_repo.listar_permissoes_usuario.return_value = []

        resp = await svc.listar_permissoes_usuario(usuario.id)

        assert resp.admin is True
        assert resp.permissoes == []


class TestConcederPermissoes:
    async def test_usuario_nao_encontrado(
        self, svc: PermissaoService, mock_usuario_repo: AsyncMock
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.conceder_permissoes(
                uuid.uuid4(),
                ConcederPermissoesRequest(
                    permissoes=[PermissaoItem(menu_chave="lancamentos", acao_chave="criar")]
                ),
                uuid.uuid4(),
            )

    async def test_menu_invalido(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = _make_usuario()
        mock_repo.get_menu_by_chave.return_value = None
        with pytest.raises(DomainError, match="não encontrado"):
            await svc.conceder_permissoes(
                uuid.uuid4(),
                ConcederPermissoesRequest(
                    permissoes=[PermissaoItem(menu_chave="inexistente", acao_chave="criar")]
                ),
                uuid.uuid4(),
            )

    async def test_acao_invalida(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = _make_usuario()
        mock_repo.get_menu_by_chave.return_value = _make_menu()
        mock_repo.get_acao_by_chave.return_value = None
        with pytest.raises(DomainError, match="não encontrada"):
            await svc.conceder_permissoes(
                uuid.uuid4(),
                ConcederPermissoesRequest(
                    permissoes=[PermissaoItem(menu_chave="lancamentos", acao_chave="inexistente")]
                ),
                uuid.uuid4(),
            )

    async def test_nao_duplica_permissao_existente(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = _make_usuario()
        mock_repo.get_menu_by_chave.return_value = _make_menu()
        mock_repo.get_acao_by_chave.return_value = _make_acao()
        mock_repo.get_permissao.return_value = MagicMock(spec=UsuarioPermissao)
        mock_repo.listar_permissoes_usuario.return_value = []

        await svc.conceder_permissoes(
            uuid.uuid4(),
            ConcederPermissoesRequest(
                permissoes=[PermissaoItem(menu_chave="lancamentos", acao_chave="criar")]
            ),
            uuid.uuid4(),
        )

        mock_repo.conceder.assert_not_awaited()

    async def test_concede_nova_permissao(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = _make_usuario()
        mock_repo.get_menu_by_chave.return_value = _make_menu()
        mock_repo.get_acao_by_chave.return_value = _make_acao()
        mock_repo.get_permissao.return_value = None
        mock_repo.conceder.side_effect = lambda p: p
        mock_repo.listar_permissoes_usuario.return_value = [
            PermissaoMatrizItem(
                permissao_id=uuid.uuid4(),
                menu_chave="lancamentos",
                menu_nome="Lançamentos",
                acao_chave="criar",
                acao_nome="Criar",
            )
        ]

        result = await svc.conceder_permissoes(
            uuid.uuid4(),
            ConcederPermissoesRequest(
                permissoes=[PermissaoItem(menu_chave="lancamentos", acao_chave="criar")]
            ),
            uuid.uuid4(),
        )

        mock_repo.conceder.assert_awaited_once()
        assert len(result) == 1


class TestRevogarPermissao:
    async def test_permissao_nao_encontrada(
        self, svc: PermissaoService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_permissao_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.revogar_permissao(uuid.uuid4(), uuid.uuid4())

    async def test_revoga_permissao(
        self, svc: PermissaoService, mock_repo: AsyncMock
    ) -> None:
        permissao = MagicMock(spec=UsuarioPermissao)
        mock_repo.get_permissao_by_id.return_value = permissao
        await svc.revogar_permissao(uuid.uuid4(), uuid.uuid4())
        mock_repo.revogar.assert_awaited_once_with(permissao)


class TestSubstituirPermissoes:
    async def test_revoga_todas_e_recria(
        self,
        svc: PermissaoService,
        mock_repo: AsyncMock,
        mock_usuario_repo: AsyncMock,
    ) -> None:
        mock_usuario_repo.get_by_id.return_value = _make_usuario()
        mock_repo.get_menu_by_chave.return_value = _make_menu()
        mock_repo.get_acao_by_chave.return_value = _make_acao()
        mock_repo.conceder.side_effect = lambda p: p
        mock_repo.listar_permissoes_usuario.return_value = []

        await svc.substituir_permissoes(
            uuid.uuid4(),
            ConcederPermissoesRequest(
                permissoes=[PermissaoItem(menu_chave="lancamentos", acao_chave="criar")]
            ),
            uuid.uuid4(),
        )

        mock_repo.revogar_todas_usuario.assert_awaited_once()
        mock_repo.conceder.assert_awaited_once()
