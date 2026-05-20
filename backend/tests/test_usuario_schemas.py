import pytest
from pydantic import ValidationError

from app.modules.usuario.schemas import (
    AlterarSenhaRequest,
    DefinirSenhaRequest,
    LoginRequest,
    UsuarioCreate,
)


class TestLoginRequest:
    def test_valido(self) -> None:
        data = LoginRequest(email="joao@exemplo.com", senha="qualquer")
        assert data.email == "joao@exemplo.com"

    def test_email_invalido(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest(email="nao-e-email", senha="qualquer")


class TestUsuarioCreate:
    def test_valido(self) -> None:
        data = UsuarioCreate(nome="João Silva", email="joao@exemplo.com", senha="senha123")
        assert data.nome == "João Silva"

    def test_nome_muito_curto(self) -> None:
        with pytest.raises(ValidationError):
            UsuarioCreate(nome="A", email="joao@exemplo.com", senha="senha123")

    def test_senha_muito_curta(self) -> None:
        with pytest.raises(ValidationError):
            UsuarioCreate(nome="João Silva", email="joao@exemplo.com", senha="abc")

    def test_email_invalido(self) -> None:
        with pytest.raises(ValidationError):
            UsuarioCreate(nome="João Silva", email="invalido", senha="senha123")


class TestAlterarSenhaRequest:
    def test_valido(self) -> None:
        data = AlterarSenhaRequest(senha_atual="antiga123", nova_senha="nova12345")
        assert data.nova_senha == "nova12345"

    def test_nova_senha_muito_curta(self) -> None:
        with pytest.raises(ValidationError):
            AlterarSenhaRequest(senha_atual="antiga123", nova_senha="abc")


class TestDefinirSenhaRequest:
    def test_valido(self) -> None:
        data = DefinirSenhaRequest(token="abc123", nova_senha="novasenha99")
        assert data.token == "abc123"

    def test_senha_muito_curta(self) -> None:
        with pytest.raises(ValidationError):
            DefinirSenhaRequest(token="abc123", nova_senha="curta")
