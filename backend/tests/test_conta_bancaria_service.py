import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import BandeiraCartao, ContaBancaria, TipoConta
from app.modules.conta_bancaria.schemas import ContaBancariaCreate, ContaBancariaUpdate
from app.modules.conta_bancaria.service import ContaBancariaService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> ContaBancariaService:
    return ContaBancariaService(mock_repo)


def _make_conta(
    tipo: TipoConta = TipoConta.CORRENTE,
    ativa: bool = True,
    usuario_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock(spec=ContaBancaria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.empresa_id = uuid.uuid4()
    c.tipo = tipo
    c.nome = "Conta Teste"
    c.banco = "Banco Teste"
    c.agencia = None
    c.numero_conta = None
    c.digito = None
    c.saldo_inicial = Decimal("0")
    c.data_saldo_inicial = None
    c.bandeira = None
    c.limite = None
    c.dia_vencimento = None
    c.dia_fechamento = None
    c.ativa = ativa
    return c


def _make_cartao(usuario_id: uuid.UUID | None = None) -> MagicMock:
    c = _make_conta(tipo=TipoConta.CARTAO_CREDITO, usuario_id=usuario_id)
    c.bandeira = BandeiraCartao.VISA
    c.limite = Decimal("5000")
    c.dia_vencimento = 10
    c.dia_fechamento = 3
    return c


class TestCriar:
    async def test_cria_corrente(self, svc: ContaBancariaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        mock_repo.create.side_effect = lambda c: c

        conta = await svc.criar(
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="BB Corrente",
                tipo=TipoConta.CORRENTE,
            ),
            u_id,
        )
        assert conta.usuario_id == u_id
        assert conta.tipo == TipoConta.CORRENTE

    async def test_cria_cartao(self, svc: ContaBancariaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        mock_repo.create.side_effect = lambda c: c

        conta = await svc.criar(
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Nubank",
                tipo=TipoConta.CARTAO_CREDITO,
                bandeira=BandeiraCartao.MASTERCARD,
                limite=Decimal("3000"),
                dia_vencimento=15,
                dia_fechamento=8,
            ),
            u_id,
        )
        assert conta.tipo == TipoConta.CARTAO_CREDITO
        assert conta.limite == Decimal("3000")


class TestObter:
    async def test_nao_encontrado(self, svc: ContaBancariaService, mock_repo: AsyncMock) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.obter(uuid.uuid4(), uuid.uuid4())

    async def test_outro_usuario_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        conta = _make_conta(usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = conta
        with pytest.raises(PermissionDeniedError):
            await svc.obter(conta.id, uuid.uuid4())


class TestAtualizar:
    async def test_atualiza_nome(self, svc: ContaBancariaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta

        await svc.atualizar(conta.id, ContaBancariaUpdate(nome="Novo Nome"), u_id)
        assert conta.nome == "Novo Nome"

    async def test_atualiza_limite_cartao(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_cartao(usuario_id=u_id)
        mock_repo.get_by_id.return_value = cartao

        await svc.atualizar(cartao.id, ContaBancariaUpdate(limite=Decimal("8000")), u_id)
        assert cartao.limite == Decimal("8000")

    async def test_zerar_limite_cartao_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_cartao(usuario_id=u_id)
        mock_repo.get_by_id.return_value = cartao

        with pytest.raises(DomainError, match="limite não pode ser removido"):
            await svc.atualizar(cartao.id, ContaBancariaUpdate(limite=None), u_id)

    async def test_corrente_com_bandeira_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(usuario_id=u_id, tipo=TipoConta.CORRENTE)
        mock_repo.get_by_id.return_value = conta

        with pytest.raises(DomainError, match="exclusivo de cartão"):
            await svc.atualizar(
                conta.id, ContaBancariaUpdate(bandeira=BandeiraCartao.VISA), u_id
            )


class TestInativar:
    async def test_ja_inativa_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta

        with pytest.raises(ConflictError, match="já está inativa"):
            await svc.inativar(conta.id, u_id)

    async def test_com_lancamentos_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta
        mock_repo.has_lancamentos.return_value = True

        with pytest.raises(DomainError, match="lançamentos vinculados"):
            await svc.inativar(conta.id, u_id)

    async def test_inativa_com_sucesso(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta
        mock_repo.has_lancamentos.return_value = False

        result = await svc.inativar(conta.id, u_id)
        assert result.ativa is False


class TestReativar:
    async def test_ja_ativa_falha(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta

        with pytest.raises(ConflictError, match="já está ativa"):
            await svc.reativar(conta.id, u_id)

    async def test_reativa_com_sucesso(
        self, svc: ContaBancariaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = conta

        result = await svc.reativar(conta.id, u_id)
        assert result.ativa is True
