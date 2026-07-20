import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.modules.certificado.models import TipoCertificado
from app.modules.pessoa.models import TipoPessoa


class PessoaBase(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    tipo: TipoPessoa = TipoPessoa.INTERNO
    setor: str | None = Field(default=None, max_length=150)
    empresa_externa: str | None = Field(default=None, max_length=200)
    telefone: str | None = Field(default=None, max_length=20)
    observacoes: str | None = None


class PessoaCreate(PessoaBase):
    # Permite já associar certificados na criação.
    certificado_ids: list[uuid.UUID] = []


class PessoaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    tipo: TipoPessoa | None = None
    setor: str | None = Field(default=None, max_length=150)
    empresa_externa: str | None = Field(default=None, max_length=200)
    telefone: str | None = Field(default=None, max_length=20)
    observacoes: str | None = None


class SetCertificadosRequest(BaseModel):
    certificado_ids: list[uuid.UUID] = []


class AssociarPessoaRequest(BaseModel):
    pessoa_id: uuid.UUID


class CertificadoResumoItem(BaseModel):
    """Resumo de um certificado, para listar os que uma pessoa possui."""

    id: uuid.UUID
    nome: str
    tipo: TipoCertificado
    validade_fim: date | None
    status_validade: str
    empresa_id: uuid.UUID | None = None
    nome_empresa: str | None = None


class PessoaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    nome: str
    email: str | None
    tipo: TipoPessoa
    setor: str | None
    empresa_externa: str | None
    telefone: str | None
    observacoes: str | None
    ativo: bool
    total_certificados: int = 0


class PessoaDetalhe(PessoaResponse):
    certificados: list[CertificadoResumoItem] = []
