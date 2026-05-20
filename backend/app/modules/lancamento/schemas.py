import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.modules.lancamento.models import FrequenciaRecorrencia, StatusLancamento, TipoLancamento


class LancamentoCreate(BaseModel):
    empresa_id: uuid.UUID
    tipo: TipoLancamento
    descricao: str = Field(min_length=2, max_length=300)
    valor: Decimal = Field(gt=0)
    data_competencia: date
    data_vencimento: date
    categoria_id: uuid.UUID | None = None
    contato_id: uuid.UUID | None = None
    conta_bancaria_id: uuid.UUID | None = None
    observacoes: str | None = None


class LancamentoParceladoCreate(BaseModel):
    empresa_id: uuid.UUID
    tipo: TipoLancamento
    descricao: str = Field(min_length=2, max_length=300)
    valor_total: Decimal = Field(gt=0)
    parcelas: int = Field(ge=2, le=360)
    data_primeira_competencia: date
    data_primeiro_vencimento: date
    categoria_id: uuid.UUID | None = None
    contato_id: uuid.UUID | None = None
    conta_bancaria_id: uuid.UUID | None = None
    observacoes: str | None = None


class LancamentoRecorrenteCreate(BaseModel):
    empresa_id: uuid.UUID
    tipo: TipoLancamento
    descricao: str = Field(min_length=2, max_length=300)
    valor: Decimal = Field(gt=0)
    data_primeira_competencia: date
    data_primeiro_vencimento: date
    frequencia: FrequenciaRecorrencia
    quantidade: int = Field(ge=2, le=120)
    categoria_id: uuid.UUID | None = None
    contato_id: uuid.UUID | None = None
    conta_bancaria_id: uuid.UUID | None = None
    observacoes: str | None = None


class LancamentoBaixaCreate(BaseModel):
    valor_pago: Decimal = Field(gt=0)
    data_pagamento: date
    conta_bancaria_id: uuid.UUID
    categoria_id: uuid.UUID


class LancamentoUpdate(BaseModel):
    descricao: str | None = Field(default=None, min_length=2, max_length=300)
    valor: Decimal | None = Field(default=None, gt=0)
    data_competencia: date | None = None
    data_vencimento: date | None = None
    categoria_id: uuid.UUID | None = None
    contato_id: uuid.UUID | None = None
    observacoes: str | None = None

    @model_validator(mode="after")
    def ao_menos_um_campo(self) -> "LancamentoUpdate":
        valores = self.model_dump(exclude_unset=True)
        if not valores:
            raise ValueError("Informe ao menos um campo para atualizar.")
        return self


class LancamentoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    tipo: TipoLancamento
    descricao: str
    valor: Decimal
    valor_pago: Decimal
    data_competencia: date
    data_vencimento: date
    data_pagamento: date | None
    status: StatusLancamento
    categoria_id: uuid.UUID | None
    contato_id: uuid.UUID | None
    conta_bancaria_id: uuid.UUID | None
    fatura_id: uuid.UUID | None
    numero_parcela: int | None
    total_parcelas: int | None
    grupo_parcelas_id: uuid.UUID | None
    recorrencia_id: uuid.UUID | None
    observacoes: str | None
    ativo: bool


class LancamentoAnexoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    lancamento_id: uuid.UUID
    usuario_id: uuid.UUID
    nome_original: str
    tamanho: int
    mime_type: str
    criado_em: datetime


class ImportacaoMapeamentoPayload(BaseModel):
    descricao: str | None = None
    valor: str | None = None
    data_competencia: str | None = None
    data_vencimento: str | None = None
    observacoes: str | None = None
    categoria_id: str | None = None
    contato_id: str | None = None
    conta_bancaria_id: str | None = None


class ImportacaoLinhaPreview(BaseModel):
    numero_linha: int
    dados_originais: dict[str, str]
    payload: dict[str, str | Decimal | date | None]
    erros: list[str]
    valida: bool


class ImportacaoAnaliseResponse(BaseModel):
    colunas: list[str]
    total_linhas: int
    amostras: list[dict[str, str]]
    campos_suportados: list[str]
    campos_obrigatorios: list[str]


class ImportacaoPreviewResponse(BaseModel):
    total_linhas: int
    linhas_validas: int
    linhas_invalidas: int
    itens: list[ImportacaoLinhaPreview]


class ImportacaoResultadoResponse(BaseModel):
    total_linhas: int
    importadas: int
    ignoradas: int
