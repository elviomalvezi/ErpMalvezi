import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.empresa.models import RegimeTributario, TipoPessoa

# ─── Campos de endereço reutilizáveis ───────────────────────────────────────

class EnderecoSchema(BaseModel):
    endereco_cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: Annotated[str | None, Field(max_length=2)] = None
    pais: str = "Brasil"
    telefone: str | None = None
    email: str | None = None


# ─── Create ─────────────────────────────────────────────────────────────────

class EmpresaCreate(EnderecoSchema):
    tipo: TipoPessoa
    documento: str = Field(..., description="CNPJ (PJ) ou CPF (PF) — apenas dígitos")
    nome_principal: str = Field(..., min_length=2, max_length=200)
    nome_alternativo: str | None = None
    documento_complementar_1: str | None = None
    documento_complementar_2: str | None = None
    regime_tributario: RegimeTributario | None = None

    # Configurações financeiras (opcionais na criação)
    moeda_padrao: str = "BRL"
    simbolo_monetario: str = "R$"
    separador_decimal: str = ","
    separador_milhares: str = "."
    casas_decimais_valor: int = Field(default=2, ge=0, le=4)
    casas_decimais_percentual: int = Field(default=2, ge=0, le=4)
    mes_inicio_exercicio: int = Field(default=1, ge=1, le=12)
    dia_fechamento_mensal: int = Field(default=5, ge=1, le=28)
    prefixo_lancamento: str = Field(default="LCT-", max_length=10)
    reset_anual_numeracao: bool = False

    cor_primaria: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @model_validator(mode="after")
    def validar_campos_por_tipo(self) -> "EmpresaCreate":
        if self.separador_decimal == self.separador_milhares:
            raise ValueError(
                "Separador decimal e separador de milhares não podem ser iguais"
            )
        if self.tipo == TipoPessoa.PJ and self.regime_tributario is None:
            raise ValueError("Regime tributário é obrigatório para Pessoa Jurídica")
        if self.tipo == TipoPessoa.PF and self.documento_complementar_2 is not None:
            raise ValueError("Inscrição Municipal não se aplica a Pessoa Física")
        return self


# ─── Update ─────────────────────────────────────────────────────────────────

class EmpresaUpdate(EnderecoSchema):
    nome_principal: str | None = Field(default=None, min_length=2, max_length=200)
    nome_alternativo: str | None = None
    documento_complementar_1: str | None = None
    documento_complementar_2: str | None = None
    regime_tributario: RegimeTributario | None = None

    moeda_padrao: str | None = None
    simbolo_monetario: str | None = None
    separador_decimal: str | None = None
    separador_milhares: str | None = None
    casas_decimais_valor: int | None = Field(default=None, ge=0, le=4)
    casas_decimais_percentual: int | None = Field(default=None, ge=0, le=4)
    mes_inicio_exercicio: int | None = Field(default=None, ge=1, le=12)
    trava_fechamento_ativa: bool | None = None
    dia_fechamento_mensal: int | None = Field(default=None, ge=1, le=28)
    prefixo_lancamento: str | None = Field(default=None, max_length=10)
    reset_anual_numeracao: bool | None = None

    cor_primaria: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    email_remetente_nome: str | None = None
    email_assinatura: str | None = None
    mensagem_padrao_boleto: str | None = None
    data_inicio_uso: date | None = None

    @model_validator(mode="after")
    def validar_separadores(self) -> "EmpresaUpdate":
        sep_dec = self.separador_decimal
        sep_mil = self.separador_milhares
        if sep_dec is not None and sep_mil is not None and sep_dec == sep_mil:
            raise ValueError(
                "Separador decimal e separador de milhares não podem ser iguais"
            )
        return self


# ─── Response ────────────────────────────────────────────────────────────────

class EmpresaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoPessoa
    documento: str
    nome_principal: str
    nome_alternativo: str | None
    documento_complementar_1: str | None
    documento_complementar_2: str | None
    regime_tributario: RegimeTributario | None

    moeda_padrao: str
    simbolo_monetario: str
    separador_decimal: str
    separador_milhares: str
    casas_decimais_valor: int
    casas_decimais_percentual: int
    mes_inicio_exercicio: int
    trava_fechamento_ativa: bool
    dia_fechamento_mensal: int
    prefixo_lancamento: str
    reset_anual_numeracao: bool

    cor_primaria: str | None
    logo_url: str | None
    email_remetente_nome: str | None
    email_assinatura: str | None

    endereco_cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    pais: str
    telefone: str | None
    email: str | None

    ativa: bool
    criado_em: datetime
    atualizado_em: datetime


class EmpresaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoPessoa
    documento: str
    nome_principal: str
    nome_alternativo: str | None
    cor_primaria: str | None
    logo_url: str | None
    ativa: bool
