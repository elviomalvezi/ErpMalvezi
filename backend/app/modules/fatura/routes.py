import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.fatura.models import StatusFatura
from app.modules.fatura.repository import FaturaRepository
from app.modules.fatura.schemas import (
    FaturaCreate,
    FaturaPagamentoCreate,
    FaturaResponse,
)
from app.modules.fatura.service import FaturaService

router = APIRouter(prefix="/faturas", tags=["faturas"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> FaturaService:
    return FaturaService(FaturaRepository(db), ContaBancariaRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[FaturaResponse])
async def listar_faturas(
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
    conta_bancaria_id: Annotated[uuid.UUID | None, Query()] = None,
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    status_fatura: Annotated[StatusFatura | None, Query(alias="status")] = None,
    competencia_inicio: Annotated[date | None, Query()] = None,
    competencia_fim: Annotated[date | None, Query()] = None,
) -> list[FaturaResponse]:
    faturas = await svc.listar(
        usuario_id, conta_bancaria_id, empresa_id, status_fatura,
        competencia_inicio, competencia_fim,
    )
    return [FaturaResponse.model_validate(f) for f in faturas]


@router.post("", response_model=FaturaResponse, status_code=status.HTTP_201_CREATED)
async def criar_fatura(
    data: FaturaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
) -> FaturaResponse:
    try:
        fatura = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return FaturaResponse.model_validate(fatura)


@router.get("/{fatura_id}", response_model=FaturaResponse)
async def obter_fatura(
    fatura_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
) -> FaturaResponse:
    try:
        fatura = await svc.obter(fatura_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return FaturaResponse.model_validate(fatura)


@router.patch("/{fatura_id}/fechar", response_model=FaturaResponse)
async def fechar_fatura(
    fatura_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
) -> FaturaResponse:
    try:
        fatura = await svc.fechar_fatura(fatura_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return FaturaResponse.model_validate(fatura)


@router.patch("/{fatura_id}/reabrir", response_model=FaturaResponse)
async def reabrir_fatura(
    fatura_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
) -> FaturaResponse:
    try:
        fatura = await svc.reabrir_fatura(fatura_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return FaturaResponse.model_validate(fatura)


@router.post("/{fatura_id}/pagamento", response_model=FaturaResponse)
async def registrar_pagamento(
    fatura_id: uuid.UUID,
    data: FaturaPagamentoCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[FaturaService, Depends(_svc)],
) -> FaturaResponse:
    try:
        fatura = await svc.registrar_pagamento(fatura_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return FaturaResponse.model_validate(fatura)
