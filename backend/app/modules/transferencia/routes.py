import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.transferencia.models import StatusTransferencia
from app.modules.transferencia.repository import TransferenciaRepository
from app.modules.transferencia.schemas import TransferenciaCreate, TransferenciaResponse
from app.modules.transferencia.service import TransferenciaService

router = APIRouter(prefix="/transferencias", tags=["transferencias"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> TransferenciaService:
    return TransferenciaService(TransferenciaRepository(db), ContaBancariaRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[TransferenciaResponse])
async def listar_transferencias(
    usuario_id: CurrentUserId,
    svc: Annotated[TransferenciaService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    conta_id: Annotated[uuid.UUID | None, Query()] = None,
    status_transf: Annotated[StatusTransferencia | None, Query(alias="status")] = None,
    data_inicio: Annotated[date | None, Query()] = None,
    data_fim: Annotated[date | None, Query()] = None,
    apenas_ativas: Annotated[bool, Query()] = True,
) -> list[TransferenciaResponse]:
    transferencias = await svc.listar(
        usuario_id, empresa_id, conta_id, status_transf, data_inicio, data_fim, apenas_ativas
    )
    return [TransferenciaResponse.model_validate(t) for t in transferencias]


@router.post("", response_model=TransferenciaResponse, status_code=status.HTTP_201_CREATED)
async def criar_transferencia(
    data: TransferenciaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[TransferenciaService, Depends(_svc)],
) -> TransferenciaResponse:
    try:
        transf = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransferenciaResponse.model_validate(transf)


@router.get("/{transferencia_id}", response_model=TransferenciaResponse)
async def obter_transferencia(
    transferencia_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[TransferenciaService, Depends(_svc)],
) -> TransferenciaResponse:
    try:
        transf = await svc.obter(transferencia_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransferenciaResponse.model_validate(transf)


@router.patch("/{transferencia_id}/cancelar", response_model=TransferenciaResponse)
async def cancelar_transferencia(
    transferencia_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[TransferenciaService, Depends(_svc)],
) -> TransferenciaResponse:
    try:
        transf = await svc.cancelar(transferencia_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransferenciaResponse.model_validate(transf)
