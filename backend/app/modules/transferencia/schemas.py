import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.modules.transferencia.models import StatusTransferencia


class TransferenciaCreate(BaseModel):
    empresa_origem_id: uuid.UUID
    empresa_destino_id: uuid.UUID
    conta_origem_id: uuid.UUID
    conta_destino_id: uuid.UUID
    valor: Decimal = Field(gt=0)
    data_transferencia: date
    descricao: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validar_contas_diferentes(self) -> "TransferenciaCreate":
        if self.conta_origem_id == self.conta_destino_id:
            raise ValueError("Conta de origem e destino não podem ser a mesma.")
        return self


class TransferenciaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    usuario_id: uuid.UUID
    empresa_origem_id: uuid.UUID
    empresa_destino_id: uuid.UUID
    conta_origem_id: uuid.UUID
    conta_destino_id: uuid.UUID
    valor: Decimal
    data_transferencia: date
    descricao: str | None
    status: StatusTransferencia
    ativo: bool
