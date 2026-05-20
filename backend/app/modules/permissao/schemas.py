import uuid

from pydantic import BaseModel, ConfigDict


class MenuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chave: str
    nome: str
    ordem: int
    ativo: bool


class AcaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chave: str
    nome: str


class PermissaoItem(BaseModel):
    menu_chave: str
    acao_chave: str


class ConcederPermissoesRequest(BaseModel):
    permissoes: list[PermissaoItem]


class UsuarioPermissaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    usuario_id: uuid.UUID
    menu_id: uuid.UUID
    acao_id: uuid.UUID
    concedido_por: uuid.UUID | None


class PermissaoMatrizItem(BaseModel):
    menu_chave: str
    menu_nome: str
    acao_chave: str
    acao_nome: str
    permissao_id: uuid.UUID


class UsuarioPermissoesResponse(BaseModel):
    usuario_id: uuid.UUID
    admin: bool
    permissoes: list[PermissaoMatrizItem]
