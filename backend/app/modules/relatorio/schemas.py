from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DreLinha(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    categoria_id: str
    categoria_nome: str
    nivel: int
    parent_id: str | None
    total_atual: Decimal
    total_anterior: Decimal
    variacao_pct: float | None


class DreResponse(BaseModel):
    mes_referencia: str
    mes_anterior: str
    empresa_nome: str | None

    receitas: list[DreLinha]
    total_receitas_atual: Decimal
    total_receitas_anterior: Decimal

    despesas: list[DreLinha]
    total_despesas_atual: Decimal
    total_despesas_anterior: Decimal

    resultado_atual: Decimal
    resultado_anterior: Decimal
