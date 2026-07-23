import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.contato.cnpj_lookup import consultar_cnpj
from app.modules.contato.repository import ContatoRepository
from app.modules.contato.schemas import (
    ConsultaCnpjResponse,
    ContatoCreate,
    ContatoResponse,
    ContatoUpdate,
)
from app.modules.contato.service import ContatoService

router = APIRouter(prefix="/contatos", tags=["contatos"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> ContatoService:
    return ContatoService(ContatoRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[ContatoResponse])
async def listar_contatos(
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    eh_cliente: Annotated[bool | None, Query()] = None,
    eh_fornecedor: Annotated[bool | None, Query()] = None,
    apenas_ativas: Annotated[bool, Query()] = True,
) -> list[ContatoResponse]:
    contatos = await svc.listar(usuario_id, empresa_id, eh_cliente, eh_fornecedor, apenas_ativas)
    return [ContatoResponse.model_validate(c) for c in contatos]


@router.get("/verificar-duplicata")
async def verificar_duplicata(
    documento: Annotated[str, Query(min_length=11)],
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
    excluir_id: Annotated[uuid.UUID | None, Query()] = None,
) -> dict:
    """Verifica se já existe contato ativo com o mesmo CNPJ/CPF (dígitos apenas)."""
    doc_limpo = "".join(c for c in documento if c.isdigit())
    contatos = await svc.listar(
        usuario_id, empresa_id=None, eh_cliente=None, eh_fornecedor=None, apenas_ativas=True
    )
    duplicado = next(
        (
            c for c in contatos
            if "".join(d for d in (c.documento or "") if d.isdigit()) == doc_limpo
            and (excluir_id is None or c.id != excluir_id)
        ),
        None,
    )
    if duplicado is None:
        return {"existe": False, "contato": None}
    return {
        "existe": True,
        "contato": ContatoResponse.model_validate(duplicado).model_dump(mode="json"),
    }


@router.get("/consultar-cnpj", response_model=ConsultaCnpjResponse)
async def consultar_cnpj_route(
    cnpj: Annotated[str, Query(min_length=14, max_length=18)],
    _usuario_id: CurrentUserId,
) -> ConsultaCnpjResponse:
    """Consulta um CNPJ na BrasilAPI para autopreencher o cadastro de fornecedor."""
    try:
        dados = await consultar_cnpj(cnpj)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ConsultaCnpjResponse(**dados)


@router.post("", response_model=ContatoResponse, status_code=status.HTTP_201_CREATED)
async def criar_contato(
    data: ContatoCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        contato = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(contato)


@router.get("/{contato_id}", response_model=ContatoResponse)
async def obter_contato(
    contato_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        contato = await svc.obter(contato_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(contato)


@router.put("/{contato_id}", response_model=ContatoResponse)
async def atualizar_contato(
    contato_id: uuid.UUID,
    data: ContatoUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        contato = await svc.atualizar(contato_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(contato)


@router.patch("/{contato_id}/inativar", response_model=ContatoResponse)
async def inativar_contato(
    contato_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        contato = await svc.inativar(contato_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(contato)


@router.patch("/{contato_id}/reativar", response_model=ContatoResponse)
async def reativar_contato(
    contato_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        contato = await svc.reativar(contato_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(contato)


@router.post("/{contato_id}/merge/{destino_id}", response_model=ContatoResponse)
async def merge_contatos(
    contato_id: uuid.UUID,
    destino_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContatoService, Depends(_svc)],
) -> ContatoResponse:
    try:
        destino = await svc.merge(contato_id, destino_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContatoResponse.model_validate(destino)
