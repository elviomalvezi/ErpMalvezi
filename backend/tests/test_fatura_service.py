import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.fatura.models import Fatura, StatusFatura
from app.modules.fatura.schemas import FaturaCreate, FaturaPagamentoCreate
from app.modules.fatura.service import FaturaService, _calcular_datas_fatura

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_fatura(
    status: StatusFatura = StatusFatura.ABERTA,
    usuario_id: uuid.UUID | None = None,
) -> MagicMock:
    f = MagicMock(spec=Fatura)
    f.id = uuid.uuid4()
    f.usuario_id = usuario_id or uuid.uuid4()
    f.conta_bancaria_id = uuid.uuid4()
    f.empresa_id = uuid.uuid4()
    f.competencia = date(2024, 1, 1)
    f.data_fechamento = date(2024, 1, 3)
    f.data_vencimento = date(2024, 1, 10)
    f.status = status
    f.valor_total = Decimal("0")
    f.valor_pago = Decimal("0")
    f.data_pagamento = None
    f.conta_pagamento_id = None
    return f


def _make_cartao(usuario_id: uuid.UUID | None = None) -> MagicMock:
    c = MagicMock(spec=ContaBancaria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.empresa_id = uuid.uuid4()
    c.tipo = TipoConta.CARTAO_CREDITO
    c.dia_fechamento = 3
    c.dia_vencimento = 10
    return c


def _make_conta_corrente(usuario_id: uuid.UUID | None = None) -> MagicMock:
    c = MagicMock(spec=ContaBancaria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.tipo = TipoConta.CORRENTE
    return c


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_conta_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock, mock_conta_repo: AsyncMock) -> FaturaService:
    return FaturaService(mock_repo, mock_conta_repo)


# ──────────────────────────────────────────────────────────────────────────────
# _calcular_datas_fatura (lógica pura)
# ──────────────────────────────────────────────────────────────────────────────

class TestCalcularDatasFatura:
    def test_vencimento_mesmo_mes(self) -> None:
        competencia = date(2024, 1, 1)
        fech, venc = _calcular_datas_fatura(competencia, dia_fechamento=3, dia_vencimento=10)
        assert fech == date(2024, 1, 3)
        assert venc == date(2024, 1, 10)

    def test_vencimento_mes_seguinte(self) -> None:
        competencia = date(2024, 1, 1)
        fech, venc = _calcular_datas_fatura(competencia, dia_fechamento=20, dia_vencimento=5)
        assert fech == date(2024, 1, 20)
        assert venc == date(2024, 2, 5)

    def test_virada_de_ano(self) -> None:
        competencia = date(2024, 12, 1)
        fech, venc = _calcular_datas_fatura(competencia, dia_fechamento=20, dia_vencimento=5)
        assert fech == date(2024, 12, 20)
        assert venc == date(2025, 1, 5)

    def test_fevereiro_clampado(self) -> None:
        competencia = date(2024, 2, 1)
        fech, venc = _calcular_datas_fatura(competencia, dia_fechamento=29, dia_vencimento=31)
        # 2024 é bissexto — dia 29 existe; dia 31 clampado para 29
        assert fech == date(2024, 2, 29)
        assert venc == date(2024, 2, 29)

    def test_fevereiro_nao_bissexto(self) -> None:
        competencia = date(2023, 2, 1)
        fech, venc = _calcular_datas_fatura(competencia, dia_fechamento=28, dia_vencimento=28)
        assert fech == date(2023, 2, 28)
        assert venc == date(2023, 2, 28)


# ──────────────────────────────────────────────────────────────────────────────
# FaturaService
# ──────────────────────────────────────────────────────────────────────────────

class TestCriar:
    async def test_cria_nova_fatura(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_cartao(usuario_id=u_id)
        mock_repo.get_by_conta_competencia.return_value = None
        mock_conta_repo.get_by_id.return_value = cartao
        mock_repo.create.side_effect = lambda f: f

        fatura = await svc.criar(
            FaturaCreate(conta_bancaria_id=cartao.id, competencia=date(2024, 1, 15)),
            u_id,
        )
        assert fatura.competencia == date(2024, 1, 1)
        assert fatura.data_fechamento == date(2024, 1, 3)
        assert fatura.data_vencimento == date(2024, 1, 10)

    async def test_retorna_existente(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        existente = _make_fatura(usuario_id=u_id)
        mock_repo.get_by_conta_competencia.return_value = existente

        fatura = await svc.criar(
            FaturaCreate(
                conta_bancaria_id=existente.conta_bancaria_id,
                competencia=date(2024, 1, 1),
            ),
            u_id,
        )
        assert fatura is existente
        mock_repo.create.assert_not_called()

    async def test_conta_nao_e_cartao_falha(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        corrente = _make_conta_corrente(usuario_id=u_id)
        mock_repo.get_by_conta_competencia.return_value = None
        mock_conta_repo.get_by_id.return_value = corrente

        with pytest.raises(DomainError, match="não é um cartão"):
            await svc.criar(
                FaturaCreate(conta_bancaria_id=corrente.id, competencia=date(2024, 1, 1)),
                u_id,
            )

    async def test_conta_nao_encontrada_falha(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_conta_competencia.return_value = None
        mock_conta_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await svc.criar(
                FaturaCreate(conta_bancaria_id=uuid.uuid4(), competencia=date(2024, 1, 1)),
                uuid.uuid4(),
            )


class TestFecharReabrir:
    async def test_fechar_aberta(
        self, svc: FaturaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.ABERTA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        result = await svc.fechar_fatura(fatura.id, u_id)
        assert result.status == StatusFatura.FECHADA

    async def test_fechar_ja_fechada_falha(
        self, svc: FaturaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.FECHADA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        with pytest.raises(ConflictError):
            await svc.fechar_fatura(fatura.id, u_id)

    async def test_reabrir_fechada(
        self, svc: FaturaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.FECHADA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        result = await svc.reabrir_fatura(fatura.id, u_id)
        assert result.status == StatusFatura.ABERTA

    async def test_reabrir_paga_falha(
        self, svc: FaturaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.PAGA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        with pytest.raises(ConflictError):
            await svc.reabrir_fatura(fatura.id, u_id)


class TestRegistrarPagamento:
    async def test_pagamento_valido(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.FECHADA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura
        conta_pag = _make_conta_corrente(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = conta_pag

        result = await svc.registrar_pagamento(
            fatura.id,
            FaturaPagamentoCreate(
                conta_pagamento_id=conta_pag.id,
                data_pagamento=date(2024, 1, 10),
                valor_pago=Decimal("1500.00"),
            ),
            u_id,
        )
        assert result.status == StatusFatura.PAGA
        assert result.valor_pago == Decimal("1500.00")

    async def test_fatura_aberta_falha(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.ABERTA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        with pytest.raises(DomainError, match="Feche a fatura"):
            await svc.registrar_pagamento(
                fatura.id,
                FaturaPagamentoCreate(
                    conta_pagamento_id=uuid.uuid4(),
                    data_pagamento=date(2024, 1, 10),
                    valor_pago=Decimal("1500.00"),
                ),
                u_id,
            )

    async def test_pagar_com_cartao_falha(
        self, svc: FaturaService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.FECHADA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura
        outro_cartao = _make_cartao(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = outro_cartao

        with pytest.raises(DomainError, match="cartão de crédito"):
            await svc.registrar_pagamento(
                fatura.id,
                FaturaPagamentoCreate(
                    conta_pagamento_id=outro_cartao.id,
                    data_pagamento=date(2024, 1, 10),
                    valor_pago=Decimal("1500.00"),
                ),
                u_id,
            )

    async def test_fatura_ja_paga_falha(
        self, svc: FaturaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura = _make_fatura(status=StatusFatura.PAGA, usuario_id=u_id)
        mock_repo.get_by_id.return_value = fatura

        with pytest.raises(ConflictError, match="já está paga"):
            await svc.registrar_pagamento(
                fatura.id,
                FaturaPagamentoCreate(
                    conta_pagamento_id=uuid.uuid4(),
                    data_pagamento=date(2024, 1, 10),
                    valor_pago=Decimal("1500.00"),
                ),
                u_id,
            )


class TestObter:
    async def test_nao_encontrada(self, svc: FaturaService, mock_repo: AsyncMock) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.obter(uuid.uuid4(), uuid.uuid4())

    async def test_outro_usuario_falha(self, svc: FaturaService, mock_repo: AsyncMock) -> None:
        fatura = _make_fatura(usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = fatura
        with pytest.raises(PermissionDeniedError):
            await svc.obter(fatura.id, uuid.uuid4())
