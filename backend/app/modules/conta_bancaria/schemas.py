import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.modules.conta_bancaria.models import BandeiraCartao, TipoConta

_TIPOS_BANCARIOS = {TipoConta.CORRENTE, TipoConta.POUPANCA}


class ContaBancariaCreate(BaseModel):
    empresa_id: uuid.UUID
    nome: str = Field(min_length=2, max_length=100)
    tipo: TipoConta
    banco: str | None = Field(default=None, max_length=100)
    agencia: str | None = Field(default=None, max_length=20)
    numero_conta: str | None = Field(default=None, max_length=30)
    digito: str | None = Field(default=None, max_length=5)
    saldo_inicial: Decimal = Field(default=Decimal("0"))
    data_saldo_inicial: date | None = None

    # Cartão de crédito
    bandeira: BandeiraCartao | None = None
    limite: Decimal | None = None
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def validar_tipo(self) -> "ContaBancariaCreate":
        if self.tipo == TipoConta.CARTAO_CREDITO:
            if self.limite is None:
                raise ValueError("limite é obrigatório para cartão de crédito.")
            if self.dia_vencimento is None:
                raise ValueError("dia_vencimento é obrigatório para cartão de crédito.")
            if self.dia_fechamento is None:
                raise ValueError("dia_fechamento é obrigatório para cartão de crédito.")
        else:
            if self.bandeira is not None:
                raise ValueError("bandeira é exclusivo de cartão de crédito.")
            if self.limite is not None:
                raise ValueError("limite é exclusivo de cartão de crédito.")
            if self.dia_vencimento is not None:
                raise ValueError("dia_vencimento é exclusivo de cartão de crédito.")
            if self.dia_fechamento is not None:
                raise ValueError("dia_fechamento é exclusivo de cartão de crédito.")
        return self


class ContaBancariaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    banco: str | None = Field(default=None, max_length=100)
    agencia: str | None = Field(default=None, max_length=20)
    numero_conta: str | None = Field(default=None, max_length=30)
    digito: str | None = Field(default=None, max_length=5)
    saldo_inicial: Decimal | None = None
    data_saldo_inicial: date | None = None
    bandeira: BandeiraCartao | None = None
    limite: Decimal | None = None
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)


class ContaBancariaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    nome: str
    tipo: TipoConta
    banco: str | None
    agencia: str | None
    numero_conta: str | None
    digito: str | None
    saldo_inicial: Decimal
    data_saldo_inicial: date | None
    bandeira: BandeiraCartao | None
    limite: Decimal | None
    dia_vencimento: int | None
    dia_fechamento: int | None
    ativa: bool
