import uuid
from datetime import date
from decimal import Decimal

from app.modules.fluxo_caixa.repository import FluxoCaixaRepository
from app.modules.fluxo_caixa.schemas import FluxoCaixaResponse, PeriodoFluxo
from app.modules.lancamento.models import StatusLancamento, TipoLancamento

_ZERO = Decimal("0")


class FluxoCaixaService:
    def __init__(self, repo: FluxoCaixaRepository) -> None:
        self._repo = repo

    async def obter(
        self,
        usuario_id: uuid.UUID,
        data_inicio: date,
        data_fim: date,
        empresa_id: uuid.UUID | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> FluxoCaixaResponse:
        saldo_inicial = await self._repo.saldo_conta(usuario_id, empresa_id, conta_bancaria_id)
        rows = await self._repo.agregar_por_mes(
            usuario_id, data_inicio, data_fim, empresa_id, conta_bancaria_id
        )

        acumulado: dict[date, dict] = {}
        for row in rows:
            periodo = row["periodo"]
            if periodo not in acumulado:
                acumulado[periodo] = {
                    "receitas_realizadas": _ZERO,
                    "despesas_realizadas": _ZERO,
                    "receitas_previstas": _ZERO,
                    "despesas_previstas": _ZERO,
                }
            bucket = acumulado[periodo]
            realizado = row["status"] == StatusLancamento.PAGO
            receita = row["tipo"] == TipoLancamento.RECEITA
            total = row["total"]

            if realizado and receita:
                bucket["receitas_realizadas"] += total
            elif realizado and not receita:
                bucket["despesas_realizadas"] += total
            elif not realizado and receita:
                bucket["receitas_previstas"] += total
            else:
                bucket["despesas_previstas"] += total

        periodos = [
            PeriodoFluxo(
                periodo=p,
                receitas_realizadas=v["receitas_realizadas"],
                despesas_realizadas=v["despesas_realizadas"],
                receitas_previstas=v["receitas_previstas"],
                despesas_previstas=v["despesas_previstas"],
            )
            for p, v in sorted(acumulado.items())
        ]

        return FluxoCaixaResponse(
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            saldo_inicial=saldo_inicial,
            periodos=periodos,
        )
