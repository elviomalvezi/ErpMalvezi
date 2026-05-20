import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.patrimonio.models import (
    CombustivelVeiculo,
    StatusImovel,
    StatusVeiculo,
    TipoImovel,
)


# ─────────────────────────────────────── Veículo ─────────────────────────────


class VeiculoCreate(BaseModel):
    empresa_id: uuid.UUID
    placa: str | None = Field(default=None, max_length=10)
    renavam: str | None = Field(default=None, max_length=20)
    chassi: str | None = Field(default=None, max_length=50)
    numero_motor: str | None = Field(default=None, max_length=50)
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=150)
    ano_fabricacao: int = Field(ge=1900, le=2100)
    ano_modelo: int | None = Field(default=None, ge=1900, le=2100)
    cor: str | None = Field(default=None, max_length=50)
    combustivel: CombustivelVeiculo | None = None
    valor_aquisicao: Decimal = Field(gt=0)
    data_aquisicao: date | None = None
    valor_mercado: Decimal | None = Field(default=None, gt=0)
    quilometragem: int | None = Field(default=None, ge=0)
    observacoes: str | None = None


class VeiculoUpdate(BaseModel):
    placa: str | None = Field(default=None, max_length=10)
    renavam: str | None = Field(default=None, max_length=20)
    chassi: str | None = Field(default=None, max_length=50)
    numero_motor: str | None = Field(default=None, max_length=50)
    marca: str | None = Field(default=None, min_length=1, max_length=100)
    modelo: str | None = Field(default=None, min_length=1, max_length=150)
    ano_fabricacao: int | None = Field(default=None, ge=1900, le=2100)
    ano_modelo: int | None = Field(default=None, ge=1900, le=2100)
    cor: str | None = Field(default=None, max_length=50)
    combustivel: CombustivelVeiculo | None = None
    valor_aquisicao: Decimal | None = Field(default=None, gt=0)
    data_aquisicao: date | None = None
    valor_mercado: Decimal | None = Field(default=None, gt=0)
    quilometragem: int | None = Field(default=None, ge=0)
    status: StatusVeiculo | None = None
    observacoes: str | None = None


class VeiculoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    placa: str | None
    renavam: str | None
    chassi: str | None
    numero_motor: str | None
    marca: str
    modelo: str
    ano_fabricacao: int
    ano_modelo: int | None
    cor: str | None
    combustivel: CombustivelVeiculo | None
    valor_aquisicao: Decimal
    data_aquisicao: date | None
    valor_mercado: Decimal | None
    quilometragem: int | None
    status: StatusVeiculo
    observacoes: str | None
    ativo: bool


# ─────────────────────────────────────── Imóvel ──────────────────────────────


class ImovelCreate(BaseModel):
    empresa_id: uuid.UUID
    tipo: TipoImovel
    descricao: str = Field(min_length=2, max_length=300)
    matricula: str | None = Field(default=None, max_length=100)
    inscricao_municipal: str | None = Field(default=None, max_length=50)
    cep: str | None = Field(default=None, max_length=9)
    logradouro: str | None = Field(default=None, max_length=300)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    area_total: Decimal | None = Field(default=None, gt=0)
    area_construida: Decimal | None = Field(default=None, gt=0)
    valor_aquisicao: Decimal = Field(gt=0)
    data_aquisicao: date | None = None
    valor_mercado: Decimal | None = Field(default=None, gt=0)
    valor_venal: Decimal | None = Field(default=None, gt=0)
    observacoes: str | None = None


class ImovelUpdate(BaseModel):
    tipo: TipoImovel | None = None
    descricao: str | None = Field(default=None, min_length=2, max_length=300)
    matricula: str | None = Field(default=None, max_length=100)
    inscricao_municipal: str | None = Field(default=None, max_length=50)
    cep: str | None = Field(default=None, max_length=9)
    logradouro: str | None = Field(default=None, max_length=300)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    area_total: Decimal | None = Field(default=None, gt=0)
    area_construida: Decimal | None = Field(default=None, gt=0)
    valor_aquisicao: Decimal | None = Field(default=None, gt=0)
    data_aquisicao: date | None = None
    valor_mercado: Decimal | None = Field(default=None, gt=0)
    valor_venal: Decimal | None = Field(default=None, gt=0)
    status: StatusImovel | None = None
    observacoes: str | None = None


class ImovelResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    tipo: TipoImovel
    descricao: str
    matricula: str | None
    inscricao_municipal: str | None
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    area_total: Decimal | None
    area_construida: Decimal | None
    valor_aquisicao: Decimal
    data_aquisicao: date | None
    valor_mercado: Decimal | None
    valor_venal: Decimal | None
    status: StatusImovel
    observacoes: str | None
    ativo: bool


# ─────────────────────────────────────── Anexos ──────────────────────────────


class PatrimonioAnexoResponse(BaseModel):
    id: uuid.UUID
    registro_id: uuid.UUID
    usuario_id: uuid.UUID
    nome_original: str
    tamanho: int
    mime_type: str
    criado_em: datetime
