import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.contato.models import EscopoContato, TipoContato
from app.modules.empresa.validators import (
    normalizar_documento,
    validar_cnpj,
    validar_cpf,
)


def _validar_doc_por_tipo(documento: str, tipo: TipoContato) -> None:
    if tipo == TipoContato.PJ and not validar_cnpj(documento):
        raise ValueError("CNPJ inválido.")
    if tipo == TipoContato.PF and not validar_cpf(documento):
        raise ValueError("CPF inválido.")


class ContatoCreate(BaseModel):
    tipo: TipoContato
    documento: str | None = None
    nome_principal: str = Field(min_length=2, max_length=200)
    nome_alternativo: str | None = Field(default=None, max_length=200)
    eh_cliente: bool = True
    eh_fornecedor: bool = False
    escopo: EscopoContato = EscopoContato.GLOBAL
    empresa_id: uuid.UUID | None = None

    email: str | None = Field(default=None, max_length=320)
    telefone: str | None = Field(default=None, max_length=20)
    celular: str | None = Field(default=None, max_length=20)
    site: str | None = Field(default=None, max_length=500)

    cep: str | None = Field(default=None, max_length=9)
    logradouro: str | None = Field(default=None, max_length=200)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    pais: str = Field(default="Brasil", max_length=50)
    observacoes: str | None = None

    @field_validator("documento", mode="before")
    @classmethod
    def normalizar_doc(cls, v: Any) -> str | None:
        if v is None:
            return None
        return normalizar_documento(str(v))

    @model_validator(mode="after")
    def validar(self) -> "ContatoCreate":
        if self.documento is not None:
            _validar_doc_por_tipo(self.documento, self.tipo)

        if self.escopo == EscopoContato.ESPECIFICO and self.empresa_id is None:
            raise ValueError("empresa_id é obrigatório quando escopo é 'especifico'.")
        if self.escopo == EscopoContato.GLOBAL and self.empresa_id is not None:
            raise ValueError("empresa_id deve ser nulo quando escopo é 'global'.")
        if not self.eh_cliente and not self.eh_fornecedor:
            raise ValueError("O contato deve ser cliente, fornecedor ou ambos.")
        return self


class ContatoUpdate(BaseModel):
    documento: str | None = None
    nome_principal: str | None = Field(default=None, min_length=2, max_length=200)
    nome_alternativo: str | None = Field(default=None, max_length=200)
    eh_cliente: bool | None = None
    eh_fornecedor: bool | None = None
    escopo: EscopoContato | None = None
    empresa_id: uuid.UUID | None = None

    email: str | None = Field(default=None, max_length=320)
    telefone: str | None = Field(default=None, max_length=20)
    celular: str | None = Field(default=None, max_length=20)
    site: str | None = Field(default=None, max_length=500)

    cep: str | None = Field(default=None, max_length=9)
    logradouro: str | None = Field(default=None, max_length=200)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    pais: str | None = Field(default=None, max_length=50)
    observacoes: str | None = None

    @field_validator("documento", mode="before")
    @classmethod
    def normalizar_doc(cls, v: Any) -> str | None:
        if v is None:
            return None
        return normalizar_documento(str(v))


class ConsultaCnpjResponse(BaseModel):
    """Dados de um CNPJ consultado na BrasilAPI, prontos para preencher o contato."""

    documento: str
    nome_principal: str | None = None
    nome_alternativo: str | None = None
    email: str | None = None
    telefone: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    situacao: str | None = None


class ContatoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    usuario_id: uuid.UUID
    empresa_id: uuid.UUID | None
    tipo: TipoContato
    documento: str | None
    nome_principal: str
    nome_alternativo: str | None
    eh_cliente: bool
    eh_fornecedor: bool
    escopo: EscopoContato
    email: str | None
    telefone: str | None
    celular: str | None
    site: str | None
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    pais: str
    observacoes: str | None
    ativa: bool
