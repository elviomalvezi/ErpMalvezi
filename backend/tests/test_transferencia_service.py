import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.transferencia.models import StatusTransferencia, Transferencia
from app.modules.transferencia.schemas import TransferenciaCreate
from app.modules.transferencia.service import TransferenciaService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_conta_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock, mock_conta_repo: AsyncMock) -> TransferenciaService:
    return TransferenciaService(mock_repo, mock_conta_repo)


def _make_conta(
    tipo: TipoConta = TipoConta.CORRENTE,
    usuario_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock(spec=ContaBancaria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.tipo = tipo
    return c


def _make_transferencia(
    usuario_id: uuid.UUID | None = None,
    status: StatusTransferencia = StatusTransferencia.CONCLUIDA,
) -> MagicMock:
    t = MagicMock(spec=Transferencia)
    t.id = uuid.uuid4()
    t.usuario_id = usuario_id or uuid.uuid4()
    t.status = status
    t.ativo = True
    return t


def _make_create(
    conta_origem_id: uuid.UUID | None = None,
    conta_destino_id: uuid.UUID | None = None,
) -> TransferenciaCreate:
    return TransferenciaCreate(
        empresa_origem_id=uuid.uuid4(),
        empresa_destino_id=uuid.uuid4(),
        conta_origem_id=conta_origem_id or uuid.uuid4(),
        conta_destino_id=conta_destino_id or uuid.uuid4(),
        valor=Decimal("500"),
        data_transferencia=date(2024, 1, 15),
    )


class TestTransferenciaCreateSchema:
    def test_mesma_conta_falha(self) -> None:
        conta_id = uuid.uuid4()
        with pytest.raises(ValidationError, match="não podem ser a mesma"):
            TransferenciaCreate(
                empresa_origem_id=uuid.uuid4(),
                empresa_destino_id=uuid.uuid4(),
                conta_origem_id=conta_id,
                conta_destino_id=conta_id,
                valor=Decimal("100"),
                data_transferencia=date(2024, 1, 1),
            )

    def test_valor_zero_falha(self) -> None:
        with pytest.raises(ValidationError):
            TransferenciaCreate(
                empresa_origem_id=uuid.uuid4(),
                empresa_destino_id=uuid.uuid4(),
                conta_origem_id=uuid.uuid4(),
                conta_destino_id=uuid.uuid4(),
                valor=Decimal("0"),
                data_transferencia=date(2024, 1, 1),
            )

    def test_valido(self) -> None:
        data = TransferenciaCreate(
            empresa_origem_id=uuid.uuid4(),
            empresa_destino_id=uuid.uuid4(),
            conta_origem_id=uuid.uuid4(),
            conta_destino_id=uuid.uuid4(),
            valor=Decimal("1000"),
            data_transferencia=date(2024, 6, 1),
        )
        assert data.valor == Decimal("1000")


class TestCriar:
    async def test_cria_transferencia(
        self, svc: TransferenciaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        origem = _make_conta(usuario_id=u_id)
        destino = _make_conta(usuario_id=u_id)
        mock_conta_repo.get_by_id.side_effect = [origem, destino]
        mock_repo.create.side_effect = lambda t: t

        data = _make_create(conta_origem_id=origem.id, conta_destino_id=destino.id)
        transf = await svc.criar(data, u_id)

        assert transf.usuario_id == u_id
        assert transf.status == StatusTransferencia.CONCLUIDA
        assert transf.valor == Decimal("500")

    async def test_origem_cartao_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_conta(tipo=TipoConta.CARTAO_CREDITO, usuario_id=u_id)
        mock_conta_repo.get_by_id.side_effect = [cartao]

        with pytest.raises(DomainError, match="cartão de crédito"):
            await svc.criar(_make_create(conta_origem_id=cartao.id), u_id)

    async def test_destino_cartao_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        origem = _make_conta(usuario_id=u_id)
        cartao = _make_conta(tipo=TipoConta.CARTAO_CREDITO, usuario_id=u_id)
        mock_conta_repo.get_by_id.side_effect = [origem, cartao]

        with pytest.raises(DomainError, match="cartão de crédito"):
            await svc.criar(
                _make_create(conta_origem_id=origem.id, conta_destino_id=cartao.id), u_id
            )

    async def test_origem_outro_usuario_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        origem = _make_conta(usuario_id=uuid.uuid4())
        mock_conta_repo.get_by_id.side_effect = [origem]

        with pytest.raises(PermissionDeniedError):
            await svc.criar(_make_create(conta_origem_id=origem.id), uuid.uuid4())

    async def test_destino_outro_usuario_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        origem = _make_conta(usuario_id=u_id)
        destino = _make_conta(usuario_id=uuid.uuid4())
        mock_conta_repo.get_by_id.side_effect = [origem, destino]

        with pytest.raises(PermissionDeniedError):
            await svc.criar(
                _make_create(conta_origem_id=origem.id, conta_destino_id=destino.id), u_id
            )

    async def test_origem_nao_encontrada_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        mock_conta_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError, match="origem"):
            await svc.criar(_make_create(), uuid.uuid4())

    async def test_destino_nao_encontrado_falha(
        self, svc: TransferenciaService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        origem = _make_conta(usuario_id=u_id)
        mock_conta_repo.get_by_id.side_effect = [origem, None]
        with pytest.raises(NotFoundError, match="destino"):
            await svc.criar(
                _make_create(conta_origem_id=origem.id), u_id
            )


class TestCancelar:
    async def test_cancela_com_sucesso(
        self, svc: TransferenciaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transf = _make_transferencia(usuario_id=u_id)
        mock_repo.get_by_id.return_value = transf

        result = await svc.cancelar(transf.id, u_id)
        assert result.status == StatusTransferencia.CANCELADA
        assert result.ativo is False

    async def test_ja_cancelada_falha(
        self, svc: TransferenciaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transf = _make_transferencia(
            usuario_id=u_id, status=StatusTransferencia.CANCELADA
        )
        mock_repo.get_by_id.return_value = transf

        with pytest.raises(ConflictError, match="já está cancelada"):
            await svc.cancelar(transf.id, u_id)


class TestObter:
    async def test_nao_encontrada(
        self, svc: TransferenciaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.obter(uuid.uuid4(), uuid.uuid4())

    async def test_outro_usuario_falha(
        self, svc: TransferenciaService, mock_repo: AsyncMock
    ) -> None:
        transf = _make_transferencia(usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = transf
        with pytest.raises(PermissionDeniedError):
            await svc.obter(transf.id, uuid.uuid4())
