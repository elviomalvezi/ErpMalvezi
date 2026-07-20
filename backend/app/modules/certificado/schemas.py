import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.modules.certificado.models import TipoCertificado


class CertificadoManualCreate(BaseModel):
    """Cadastro manual (sem arquivo) — útil para registrar um vencimento avulso."""

    nome: str = Field(min_length=2, max_length=200)
    tipo: TipoCertificado = TipoCertificado.OUTRO
    empresa_id: uuid.UUID | None = None
    titular: str | None = Field(default=None, max_length=300)
    documento: str | None = Field(default=None, max_length=20)
    emissor: str | None = Field(default=None, max_length=300)
    numero_serie: str | None = Field(default=None, max_length=100)
    validade_inicio: date | None = None
    validade_fim: date | None = None
    observacoes: str | None = None


class CertificadoUpdate(BaseModel):
    # As datas de validade NÃO entram aqui: após a inclusão elas são imutáveis
    # (extraídas do certificado / definidas no cadastro). Evita adulterar o vencimento.
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    tipo: TipoCertificado | None = None
    empresa_id: uuid.UUID | None = None
    titular: str | None = Field(default=None, max_length=300)
    documento: str | None = Field(default=None, max_length=20)
    emissor: str | None = Field(default=None, max_length=300)
    numero_serie: str | None = Field(default=None, max_length=100)
    observacoes: str | None = None


class CertificadoResumo(BaseModel):
    total: int
    validos: int
    vencendo: int
    vencido: int


class CertificadoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    empresa_id: uuid.UUID | None
    nome_empresa: str | None = None
    nome: str
    tipo: TipoCertificado
    titular: str | None
    documento: str | None
    emissor: str | None
    numero_serie: str | None
    validade_inicio: date | None
    validade_fim: date | None
    formato: str | None
    arquivo_nome: str | None
    tem_arquivo: bool = False
    tem_senha: bool = False
    observacoes: str | None
    ativo: bool
    # Computados
    dias_para_vencer: int | None = None
    status_validade: str = "sem_data"  # valido | vencendo | vencido | sem_data
