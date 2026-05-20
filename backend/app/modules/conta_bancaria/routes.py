import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.conta_bancaria.schemas import (
    ContaBancariaCreate,
    ContaBancariaResponse,
    ContaBancariaUpdate,
)
from app.modules.conta_bancaria.service import ContaBancariaService

router = APIRouter(prefix="/contas-bancarias", tags=["contas-bancarias"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> ContaBancariaService:
    return ContaBancariaService(ContaBancariaRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[ContaBancariaResponse])
async def listar_contas(
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    tipo: Annotated[TipoConta | None, Query()] = None,
    apenas_ativas: Annotated[bool, Query()] = True,
) -> list[ContaBancariaResponse]:
    contas = await svc.listar(usuario_id, empresa_id, tipo, apenas_ativas)
    return [ContaBancariaResponse.model_validate(c) for c in contas]


@router.post("", response_model=ContaBancariaResponse, status_code=status.HTTP_201_CREATED)
async def criar_conta(
    data: ContaBancariaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
) -> ContaBancariaResponse:
    try:
        conta = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContaBancariaResponse.model_validate(conta)


@router.get("/{conta_id}", response_model=ContaBancariaResponse)
async def obter_conta(
    conta_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
) -> ContaBancariaResponse:
    try:
        conta = await svc.obter(conta_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContaBancariaResponse.model_validate(conta)


@router.put("/{conta_id}", response_model=ContaBancariaResponse)
async def atualizar_conta(
    conta_id: uuid.UUID,
    data: ContaBancariaUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
) -> ContaBancariaResponse:
    try:
        conta = await svc.atualizar(conta_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContaBancariaResponse.model_validate(conta)


@router.patch("/{conta_id}/inativar", response_model=ContaBancariaResponse)
async def inativar_conta(
    conta_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
) -> ContaBancariaResponse:
    try:
        conta = await svc.inativar(conta_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContaBancariaResponse.model_validate(conta)


@router.patch("/{conta_id}/reativar", response_model=ContaBancariaResponse)
async def reativar_conta(
    conta_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ContaBancariaService, Depends(_svc)],
) -> ContaBancariaResponse:
    try:
        conta = await svc.reativar(conta_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ContaBancariaResponse.model_validate(conta)
