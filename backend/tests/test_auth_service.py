import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import hash_password
from app.modules.usuario.models import Sessao, TokenSeguranca, Usuario
from app.modules.usuario.repository import MAX_TENTATIVAS
from app.modules.usuario.schemas import (
    DefinirSenhaRequest,
    LoginRequest,
    UsuarioCreate,
)
from app.modules.usuario.service import AuthError, ContaBloqueadaError, UsuarioService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> UsuarioService:
    return UsuarioService(mock_repo)


class TestLogin:
    async def test_conta_bloqueada(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        mock_repo.count_tentativas_recentes.return_value = MAX_TENTATIVAS
        with pytest.raises(ContaBloqueadaError):
            await svc.login(LoginRequest(email="a@b.com", senha="qualquer"))

    async def test_email_nao_encontrado(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.count_tentativas_recentes.return_value = 0
        mock_repo.get_by_email.return_value = None
        with pytest.raises(AuthError, match="inválidos"):
            await svc.login(LoginRequest(email="a@b.com", senha="qualquer"))
        mock_repo.registrar_tentativa.assert_awaited_once()

    async def test_senha_errada(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        mock_repo.count_tentativas_recentes.return_value = 0
        usuario = MagicMock(spec=Usuario)
        usuario.ativo = True
        usuario.senha_hash = hash_password("correta123")
        mock_repo.get_by_email.return_value = usuario
        with pytest.raises(AuthError, match="inválidos"):
            await svc.login(LoginRequest(email="a@b.com", senha="errada"))
        mock_repo.registrar_tentativa.assert_awaited_once()

    async def test_usuario_inativo(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        mock_repo.count_tentativas_recentes.return_value = 0
        usuario = MagicMock(spec=Usuario)
        usuario.ativo = False
        usuario.senha_hash = hash_password("senha123")
        mock_repo.get_by_email.return_value = usuario
        with pytest.raises(AuthError, match="inativo"):
            await svc.login(LoginRequest(email="a@b.com", senha="senha123"))

    async def test_sucesso_retorna_token(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.count_tentativas_recentes.return_value = 0
        usuario = MagicMock(spec=Usuario)
        usuario.id = uuid.uuid4()
        usuario.nome = "Teste"
        usuario.ativo = True
        usuario.senha_hash = hash_password("senha123")
        usuario.token_version = 0  # claim "tv" do JWT precisa ser serializável
        mock_repo.get_by_email.return_value = usuario
        mock_repo.criar_sessao.return_value = MagicMock(spec=Sessao)

        token = await svc.login(LoginRequest(email="a@b.com", senha="senha123"))

        assert isinstance(token, str)
        assert len(token) > 20
        mock_repo.registrar_tentativa.assert_awaited_once()
        mock_repo.criar_sessao.assert_awaited_once()


class TestLogout:
    async def test_revoga_sessao(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        jti = str(uuid.uuid4())
        await svc.logout(jti)
        mock_repo.revogar_sessao.assert_awaited_once_with(jti)


class TestCriarUsuario:
    async def test_email_duplicado(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        from app.core.exceptions import ConflictError

        mock_repo.get_by_email.return_value = MagicMock(spec=Usuario)
        with pytest.raises(ConflictError):
            await svc.criar_usuario(
                UsuarioCreate(nome="Novo", email="existe@b.com", senha="senha123")
            )

    async def test_cria_com_senha_hasheada(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: u

        usuario = await svc.criar_usuario(
            UsuarioCreate(nome="Novo User", email="novo@b.com", senha="senha123")
        )

        assert usuario.email == "novo@b.com"
        assert usuario.senha_hash != "senha123"
        assert usuario.senha_hash.startswith("$2b$")


class TestRecuperarSenha:
    async def test_email_inexistente_nao_levanta(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_email.return_value = None
        await svc.recuperar_senha("naoexiste@b.com")
        mock_repo.criar_token.assert_not_awaited()

    async def test_cria_token_e_tenta_enviar_email(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        usuario = MagicMock(spec=Usuario)
        usuario.id = uuid.uuid4()
        usuario.nome = "Fulano"
        usuario.email = "fulano@b.com"
        mock_repo.get_by_email.return_value = usuario
        mock_repo.criar_token.return_value = MagicMock(spec=TokenSeguranca)

        with patch("app.modules.usuario.service.smtp_sender.send") as mock_send:
            mock_send.side_effect = ConnectionRefusedError("sem SMTP")
            await svc.recuperar_senha("fulano@b.com")

        mock_repo.criar_token.assert_awaited_once()


class TestDefinirSenha:
    async def test_token_invalido(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        from app.core.exceptions import NotFoundError

        mock_repo.get_token_by_hash.return_value = None
        with pytest.raises(NotFoundError):
            await svc.definir_senha(DefinirSenhaRequest(token="invalido", nova_senha="nova12345"))

    async def test_token_ja_usado(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        from app.core.exceptions import NotFoundError

        token = MagicMock(spec=TokenSeguranca)
        token.usado_em = datetime.now(UTC)
        mock_repo.get_token_by_hash.return_value = token
        with pytest.raises(NotFoundError, match="já utilizado"):
            await svc.definir_senha(DefinirSenhaRequest(token="qualquer", nova_senha="nova12345"))

    async def test_token_expirado(self, svc: UsuarioService, mock_repo: AsyncMock) -> None:
        from app.core.exceptions import DomainError

        token = MagicMock(spec=TokenSeguranca)
        token.usado_em = None
        token.expira_em = datetime.now(UTC) - timedelta(hours=1)
        mock_repo.get_token_by_hash.return_value = token
        with pytest.raises(DomainError, match="expirado"):
            await svc.definir_senha(DefinirSenhaRequest(token="qualquer", nova_senha="nova12345"))

    async def test_sucesso_atualiza_senha(
        self, svc: UsuarioService, mock_repo: AsyncMock
    ) -> None:
        token = MagicMock(spec=TokenSeguranca)
        token.usado_em = None
        token.expira_em = datetime.now(UTC) + timedelta(hours=1)
        token.usuario_id = uuid.uuid4()
        mock_repo.get_token_by_hash.return_value = token

        usuario = MagicMock(spec=Usuario)
        usuario.id = token.usuario_id
        mock_repo.get_by_id.return_value = usuario

        await svc.definir_senha(DefinirSenhaRequest(token="qualquer", nova_senha="novasenha99"))

        assert usuario.senha_hash.startswith("$2b$")
        assert token.usado_em is not None
        mock_repo.revogar_todas_sessoes_usuario.assert_awaited_once_with(usuario.id)
