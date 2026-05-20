import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.fatura.models import StatusFatura


class FaturaCreate(BaseModel):
    conta_bancaria_id: uuid.UUID
    competencia: date  # qualquer dia do mês — normalizado para o dia 1

    @field_validator("competencia", mode="after")
    @classmethod
    def normalizar_competencia(cls, v: date) -> date:
        return v.replace(day=1)


class FaturaPagamentoCreate(BaseModel):
    conta_pagamento_id: uuid.UUID
    data_pagamento: date
    valor_pago: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def validar_valor(self) -> "FaturaPagamentoCreate":
        if self.valor_pago <= 0:
            raise ValueError("valor_pago deve ser maior que zero.")
        return self


class FaturaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conta_bancaria_id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    competencia: date
    data_fechamento: date
    data_vencimento: date
    status: StatusFatura
    valor_total: Decimal
    valor_pago: Decimal
    data_pagamento: date | None
    conta_pagamento_id: uuid.UUID | None
