import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.conciliacao.models import StatusImportacao, StatusTransacao, TipoTransacao
from app.modules.lancamento.models import TipoLancamento


class ConfigCSV(BaseModel):
    delimiter: str = Field(default=";", max_length=1)
    col_data: int = Field(default=0, ge=0)
    col_descricao: int = Field(default=1, ge=0)
    col_valor: int = Field(default=2, ge=0)
    decimal_sep: str = Field(default=",", pattern=r"^[,.]$")
    formato_data: str = Field(default="%d/%m/%Y")
    col_tipo: int | None = Field(default=None, ge=0)
    encoding: str = Field(default="latin-1")
    skip_header: bool = True


class ImportacaoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    conta_bancaria_id: uuid.UUID
    empresa_id: uuid.UUID
    nome_arquivo: str
    status: StatusImportacao
    total_transacoes: int
    conciliadas: int
    ignoradas: int


class TransacaoBancariaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    importacao_id: uuid.UUID
    conta_bancaria_id: uuid.UUID
    empresa_id: uuid.UUID
    id_externo: str | None
    data: date
    valor: Decimal
    tipo: TipoTransacao
    descricao_original: str
    status: StatusTransacao
    lancamento_id: uuid.UUID | None


class ConciliarRequest(BaseModel):
    lancamento_id: uuid.UUID


class CriarLancamentoRequest(BaseModel):
    empresa_id: uuid.UUID
    descricao: str = Field(max_length=300)
    tipo: TipoLancamento
    data_competencia: date
    data_vencimento: date
    categoria_id: uuid.UUID
    contato_id: uuid.UUID | None = None
    observacoes: str | None = Field(default=None, max_length=1000)


class RegraCategorizacaoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    padrao: str
    categoria_id: uuid.UUID | None
    tipo_lancamento: TipoLancamento | None
    contato_id: uuid.UUID | None
    contador: int


class SugestaoMatchResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    descricao: str
    valor: Decimal
    data_vencimento: date
    tipo: TipoLancamento
