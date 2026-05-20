import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.modules.fluxo_caixa.service import FluxoCaixaService
from app.modules.lancamento.models import StatusLancamento, TipoLancamento


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> FluxoCaixaService:
    return FluxoCaixaService(mock_repo)


def _row(
    periodo: date,
    tipo: TipoLancamento,
    status: StatusLancamento,
    total: str,
) -> dict:
    return {"periodo": periodo, "tipo": tipo, "status": status, "total": Decimal(total)}


class TestFluxoCaixa:
    async def test_sem_lancamentos(self, svc: FluxoCaixaService, mock_repo: AsyncMock) -> None:
        mock_repo.saldo_conta.return_value = Decimal("1000")
        mock_repo.agregar_por_mes.return_value = []

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 3, 31))

        assert result.saldo_inicial == Decimal("1000")
        assert result.periodos == []

    async def test_periodo_receita_realizada(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("0")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 1, 1), TipoLancamento.RECEITA, StatusLancamento.PAGO, "3000"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31))

        assert len(result.periodos) == 1
        p = result.periodos[0]
        assert p.receitas_realizadas == Decimal("3000")
        assert p.despesas_realizadas == Decimal("0")
        assert p.saldo_realizado == Decimal("3000")

    async def test_periodo_despesa_realizada(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("0")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 1, 1), TipoLancamento.DESPESA, StatusLancamento.PAGO, "500"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31))

        p = result.periodos[0]
        assert p.despesas_realizadas == Decimal("500")
        assert p.saldo_realizado == Decimal("-500")

    async def test_periodo_receita_prevista(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("0")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 2, 1), TipoLancamento.RECEITA, StatusLancamento.PENDENTE, "1000"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 2, 1), date(2024, 2, 29))

        p = result.periodos[0]
        assert p.receitas_previstas == Decimal("1000")
        assert p.saldo_previsto == Decimal("1000")

    async def test_multiplos_periodos_ordenados(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("500")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 2, 1), TipoLancamento.RECEITA, StatusLancamento.PAGO, "2000"),
            _row(date(2024, 1, 1), TipoLancamento.DESPESA, StatusLancamento.PAGO, "300"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 2, 29))

        assert len(result.periodos) == 2
        assert result.periodos[0].periodo == date(2024, 1, 1)
        assert result.periodos[1].periodo == date(2024, 2, 1)

    async def test_saldo_final_projetado(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("1000")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 1, 1), TipoLancamento.RECEITA, StatusLancamento.PAGO, "500"),
            _row(date(2024, 1, 1), TipoLancamento.DESPESA, StatusLancamento.PAGO, "200"),
            _row(date(2024, 2, 1), TipoLancamento.RECEITA, StatusLancamento.PENDENTE, "800"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 2, 29))

        # 1000 + (500 - 200) + (800) = 2100
        assert result.saldo_final_projetado == Decimal("2100")

    async def test_mesmo_periodo_acumula(
        self, svc: FluxoCaixaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.saldo_conta.return_value = Decimal("0")
        mock_repo.agregar_por_mes.return_value = [
            _row(date(2024, 1, 1), TipoLancamento.RECEITA, StatusLancamento.PAGO, "1000"),
            _row(date(2024, 1, 1), TipoLancamento.DESPESA, StatusLancamento.PAGO, "400"),
            _row(date(2024, 1, 1), TipoLancamento.RECEITA, StatusLancamento.PENDENTE, "600"),
            _row(date(2024, 1, 1), TipoLancamento.DESPESA, StatusLancamento.PENDENTE, "100"),
        ]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31))

        assert len(result.periodos) == 1
        p = result.periodos[0]
        assert p.receitas_realizadas == Decimal("1000")
        assert p.despesas_realizadas == Decimal("400")
        assert p.receitas_previstas == Decimal("600")
        assert p.despesas_previstas == Decimal("100")
        assert p.saldo_periodo == Decimal("1100")
