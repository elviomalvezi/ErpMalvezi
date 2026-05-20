import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class KpiLancamentos(BaseModel):
    receitas_realizadas: Decimal
    despesas_realizadas: Decimal
    receitas_previstas: Decimal
    despesas_previstas: Decimal
    saldo_realizado: Decimal
    saldo_previsto: Decimal


class LancamentoPendente(BaseModel):
    id: uuid.UUID
    descricao: str
    valor: Decimal
    data_vencimento: date
    tipo: str


class DashboardResponse(BaseModel):
    empresa_id: uuid.UUID | None
    data_inicio: date
    data_fim: date
    saldo_contas: Decimal
    kpi: KpiLancamentos
    a_vencer_hoje: list[LancamentoPendente]
    vencidos: list[LancamentoPendente]
    proximos_vencimentos: list[LancamentoPendente]
