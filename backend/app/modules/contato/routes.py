import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.contato.repository import ContatoRepository
from app.modules.contato.schemas import ContatoCreate, ContatoResponse, ContatoUpdate
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
