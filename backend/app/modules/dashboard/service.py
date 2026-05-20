import uuid
from datetime import date
from decimal import Decimal

from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import DashboardResponse, KpiLancamentos, LancamentoPendente
from app.modules.lancamento.models import StatusLancamento, TipoLancamento

_ZERO = Decimal("0")


class DashboardService:
    def __init__(self, repo: DashboardRepository) -> None:
        self._repo = repo

    async def obter(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        data_referencia: date,
        empresa_id: uuid.UUID | None = None,
    ) -> DashboardResponse:
        kpi_rows = await self._repo.kpi_lancamentos(usuario_id, data_inicio, data_fim, empresa_id)
        saldo = await self._repo.saldo_contas(usuario_id, empresa_id)
        a_vencer = await self._repo.lancamentos_vencendo(usuario_id, data_referencia, empresa_id)
        vencidos = await self._repo.lancamentos_vencidos(usuario_id, data_referencia, empresa_id)
        proximos = await self._repo.proximos_vencimentos(usuario_id, data_referencia, empresa_id)

        rec_real = _ZERO
        desp_real = _ZERO
        rec_prev = _ZERO
        desp_prev = _ZERO

        for row in kpi_rows:
            realizado = row["status"] == StatusLancamento.PAGO
            receita = row["tipo"] == TipoLancamento.RECEITA
            total = row["total"]
            if realizado and receita:
                rec_real += total
            elif realizado:
                desp_real += total
            elif receita:
                rec_prev += total
            else:
                desp_prev += total

        kpi = KpiLancamentos(
            receitas_realizadas=rec_real,
            despesas_realizadas=desp_real,
            receitas_previstas=rec_prev,
            despesas_previstas=desp_prev,
            saldo_realizado=rec_real - desp_real,
            saldo_previsto=rec_prev - desp_prev,
        )

        def _to_pendente(lct) -> LancamentoPendente:  # type: ignore[return]
            return LancamentoPendente(
                id=lct.id,
                descricao=lct.descricao,
                valor=lct.valor,
                data_vencimento=lct.data_vencimento,
                tipo=str(lct.tipo),
            )

        return DashboardResponse(
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            saldo_contas=saldo,
            kpi=kpi,
            a_vencer_hoje=[_to_pendente(lct) for lct in a_vencer],
            vencidos=[_to_pendente(lct) for lct in vencidos],
            proximos_vencimentos=[_to_pendente(lct) for lct in proximos],
        )
