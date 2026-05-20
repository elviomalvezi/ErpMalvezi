import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PeriodoFluxo(BaseModel):
    periodo: date
    receitas_realizadas: Decimal
    despesas_realizadas: Decimal
    receitas_previstas: Decimal
    despesas_previstas: Decimal

    @property
    def saldo_realizado(self) -> Decimal:
        return self.receitas_realizadas - self.despesas_realizadas

    @property
    def saldo_previsto(self) -> Decimal:
        return self.receitas_previstas - self.despesas_previstas

    @property
    def saldo_periodo(self) -> Decimal:
        return self.saldo_realizado + self.saldo_previsto


class FluxoCaixaResponse(BaseModel):
    empresa_id: uuid.UUID | None
    data_inicio: date
    data_fim: date
    saldo_inicial: Decimal
    periodos: list[PeriodoFluxo]

    @property
    def saldo_final_projetado(self) -> Decimal:
        total = self.saldo_inicial
        for p in self.periodos:
            total += p.saldo_periodo
        return total
