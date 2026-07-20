import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.pessoa.repository import PessoaRepository
from app.modules.pessoa.schemas import (
    AssociarPessoaRequest,
    PessoaCreate,
    PessoaDetalhe,
    PessoaResponse,
    PessoaUpdate,
    SetCertificadosRequest,
)
from app.modules.pessoa.service import PessoaService

router = APIRouter(prefix="/pessoas", tags=["pessoas"])
# Endpoints de associação a partir do certificado.
router_certificado = APIRouter(prefix="/certificados", tags=["certificados"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> PessoaService:
    return PessoaService(PessoaRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[PessoaResponse])
async def listar_pessoas(
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
    apenas_ativos: Annotated[bool, Query()] = True,
) -> list[PessoaResponse]:
    return await svc.listar(usuario_id, apenas_ativos)


@router.post("", response_model=PessoaResponse, status_code=status.HTTP_201_CREATED)
async def criar_pessoa(
    data: PessoaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> PessoaResponse:
    try:
        return await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.get("/{pessoa_id}", response_model=PessoaDetalhe)
async def obter_pessoa(
    pessoa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> PessoaDetalhe:
    try:
        return await svc.obter(pessoa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.put("/{pessoa_id}", response_model=PessoaResponse)
async def atualizar_pessoa(
    pessoa_id: uuid.UUID,
    data: PessoaUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> PessoaResponse:
    try:
        return await svc.atualizar(pessoa_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.patch("/{pessoa_id}/inativar", response_model=PessoaResponse)
async def inativar_pessoa(
    pessoa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> PessoaResponse:
    try:
        return await svc.inativar(pessoa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.put("/{pessoa_id}/certificados", response_model=PessoaDetalhe)
async def definir_certificados(
    pessoa_id: uuid.UUID,
    data: SetCertificadosRequest,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> PessoaDetalhe:
    try:
        return await svc.definir_certificados(pessoa_id, data.certificado_ids, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


# ── Associação a partir do certificado ─────────────────────────────────────────
@router_certificado.get("/{certificado_id}/pessoas", response_model=list[PessoaResponse])
async def pessoas_do_certificado(
    certificado_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> list[PessoaResponse]:
    try:
        return await svc.pessoas_do_certificado(certificado_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router_certificado.post("/{certificado_id}/pessoas", status_code=status.HTTP_204_NO_CONTENT)
async def associar_pessoa(
    certificado_id: uuid.UUID,
    data: AssociarPessoaRequest,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> None:
    try:
        await svc.associar_pessoa(certificado_id, data.pessoa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router_certificado.delete(
    "/{certificado_id}/pessoas/{pessoa_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def desassociar_pessoa(
    certificado_id: uuid.UUID,
    pessoa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[PessoaService, Depends(_svc)],
) -> None:
    try:
        await svc.desassociar_pessoa(certificado_id, pessoa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
