import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.categoria.models import EscopoCategoria, TipoCategoria


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    tipo: TipoCategoria
    escopo: EscopoCategoria = EscopoCategoria.GLOBAL
    parent_id: uuid.UUID | None = None
    empresa_id: uuid.UUID | None = None
    codigo: str | None = Field(default=None, max_length=20)
    descricao: str | None = None
    exigir_veiculo: bool = False
    exigir_imovel: bool = False

    @model_validator(mode="after")
    def validate_escopo_empresa(self) -> "CategoriaCreate":
        if self.escopo == EscopoCategoria.ESPECIFICO and self.empresa_id is None:
            raise ValueError("empresa_id é obrigatório para categorias com escopo específico.")
        if self.escopo == EscopoCategoria.GLOBAL and self.empresa_id is not None:
            raise ValueError("empresa_id deve ser nulo para categorias com escopo global.")
        return self


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    parent_id: uuid.UUID | None = Field(default=None)
    codigo: str | None = Field(default=None, max_length=20)
    descricao: str | None = None
    exigir_veiculo: bool | None = None
    exigir_imovel: bool | None = None


class CategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    usuario_id: uuid.UUID
    empresa_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    nome: str
    tipo: str
    escopo: str
    nivel: int
    codigo: str | None
    descricao: str | None
    exigir_veiculo: bool
    exigir_imovel: bool
    ativa: bool


class CategoriaTreeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parent_id: uuid.UUID | None
    nome: str
    tipo: str
    escopo: str
    nivel: int
    codigo: str | None
    exigir_veiculo: bool
    exigir_imovel: bool
    ativa: bool
    filhos: list["CategoriaTreeNode"] = []
