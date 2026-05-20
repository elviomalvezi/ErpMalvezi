import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.dashboard.service import DashboardService
from app.modules.lancamento.models import StatusLancamento, TipoLancamento


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> DashboardService:
    return DashboardService(mock_repo)


def _row(tipo: TipoLancamento, status: StatusLancamento, total: str) -> dict:
    return {"tipo": tipo, "status": status, "total": Decimal(total)}


def _make_lancamento(
    descricao: str = "Teste",
    valor: str = "100",
    data_vencimento: date = date(2024, 1, 15),
    tipo: TipoLancamento = TipoLancamento.DESPESA,
) -> MagicMock:
    lct = MagicMock()
    lct.id = uuid.uuid4()
    lct.descricao = descricao
    lct.valor = Decimal(valor)
    lct.data_vencimento = data_vencimento
    lct.tipo = tipo
    return lct


class TestDashboard:
    async def test_kpi_sem_lancamentos(
        self, svc: DashboardService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.kpi_lancamentos.return_value = []
        mock_repo.saldo_contas.return_value = Decimal("5000")
        mock_repo.lancamentos_vencendo.return_value = []
        mock_repo.lancamentos_vencidos.return_value = []
        mock_repo.proximos_vencimentos.return_value = []

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 15))

        assert result.saldo_contas == Decimal("5000")
        assert result.kpi.receitas_realizadas == Decimal("0")
        assert result.kpi.despesas_realizadas == Decimal("0")
        assert result.kpi.saldo_realizado == Decimal("0")

    async def test_kpi_com_receitas_despesas(
        self, svc: DashboardService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.kpi_lancamentos.return_value = [
            _row(TipoLancamento.RECEITA, StatusLancamento.PAGO, "3000"),
            _row(TipoLancamento.DESPESA, StatusLancamento.PAGO, "1200"),
            _row(TipoLancamento.RECEITA, StatusLancamento.PENDENTE, "500"),
            _row(TipoLancamento.DESPESA, StatusLancamento.PENDENTE, "200"),
        ]
        mock_repo.saldo_contas.return_value = Decimal("0")
        mock_repo.lancamentos_vencendo.return_value = []
        mock_repo.lancamentos_vencidos.return_value = []
        mock_repo.proximos_vencimentos.return_value = []

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 15))

        assert result.kpi.receitas_realizadas == Decimal("3000")
        assert result.kpi.despesas_realizadas == Decimal("1200")
        assert result.kpi.saldo_realizado == Decimal("1800")
        assert result.kpi.receitas_previstas == Decimal("500")
        assert result.kpi.despesas_previstas == Decimal("200")
        assert result.kpi.saldo_previsto == Decimal("300")

    async def test_listas_lancamentos(
        self, svc: DashboardService, mock_repo: AsyncMock
    ) -> None:
        lct_hoje = _make_lancamento("Hoje", "100", date(2024, 1, 15))
        lct_vencido = _make_lancamento("Vencido", "200", date(2024, 1, 10))
        lct_proximo = _make_lancamento("Próximo", "300", date(2024, 1, 20))

        mock_repo.kpi_lancamentos.return_value = []
        mock_repo.saldo_contas.return_value = Decimal("0")
        mock_repo.lancamentos_vencendo.return_value = [lct_hoje]
        mock_repo.lancamentos_vencidos.return_value = [lct_vencido]
        mock_repo.proximos_vencimentos.return_value = [lct_proximo]

        result = await svc.obter(uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 15))

        assert len(result.a_vencer_hoje) == 1
        assert result.a_vencer_hoje[0].descricao == "Hoje"
        assert len(result.vencidos) == 1
        assert len(result.proximos_vencimentos) == 1

    async def test_empresa_id_passado(
        self, svc: DashboardService, mock_repo: AsyncMock
    ) -> None:
        empresa_id = uuid.uuid4()
        mock_repo.kpi_lancamentos.return_value = []
        mock_repo.saldo_contas.return_value = Decimal("0")
        mock_repo.lancamentos_vencendo.return_value = []
        mock_repo.lancamentos_vencidos.return_value = []
        mock_repo.proximos_vencimentos.return_value = []

        result = await svc.obter(
            uuid.uuid4(), date(2024, 1, 1), date(2024, 1, 31), date(2024, 1, 15), empresa_id
        )

        assert result.empresa_id == empresa_id
        mock_repo.kpi_lancamentos.assert_called_once()
        call_kwargs = mock_repo.kpi_lancamentos.call_args
        assert empresa_id in call_kwargs.args or empresa_id in call_kwargs.kwargs.values()
