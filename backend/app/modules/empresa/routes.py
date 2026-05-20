import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.core.storage import StorageProvider, get_storage_provider
from app.modules.empresa.schemas import (
    EmpresaCreate,
    EmpresaListItem,
    EmpresaResponse,
    EmpresaUpdate,
)
from app.modules.empresa.service import EmpresaService

router = APIRouter(prefix="/empresas", tags=["empresas"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> EmpresaService:
    return EmpresaService(db)


def _handle_domain(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.post("", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def criar_empresa(
    data: EmpresaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> EmpresaResponse:
    try:
        empresa = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)


@router.get("", response_model=list[EmpresaListItem])
async def listar_empresas(
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> list[EmpresaListItem]:
    empresas = await svc.listar_por_usuario(usuario_id)
    return [EmpresaListItem.model_validate(e) for e in empresas]


@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(
    empresa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> EmpresaResponse:
    try:
        empresa = await svc.obter(empresa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)


@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(
    empresa_id: uuid.UUID,
    data: EmpresaUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> EmpresaResponse:
    try:
        empresa = await svc.atualizar(empresa_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)


@router.patch("/{empresa_id}/inativar", response_model=EmpresaResponse)
async def inativar_empresa(
    empresa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> EmpresaResponse:
    try:
        empresa = await svc.inativar(empresa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)


_EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "svg"}


@router.patch("/{empresa_id}/logo", response_model=EmpresaResponse)
async def upload_logo(
    empresa_id: uuid.UUID,
    arquivo: UploadFile,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> EmpresaResponse:
    content_type = arquivo.content_type or ""
    extensao = (arquivo.filename or "logo.jpg").rsplit(".", 1)[-1].lower()
    if extensao not in _EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato não permitido. Use: {', '.join(_EXTENSOES_PERMITIDAS)}",
        )
    conteudo = await arquivo.read()
    try:
        empresa = await svc.atualizar_logo(
            empresa_id, usuario_id, conteudo, extensao, content_type, storage
        )
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)


@router.patch("/{empresa_id}/reativar", response_model=EmpresaResponse)
async def reativar_empresa(
    empresa_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[EmpresaService, Depends(_svc)],
) -> EmpresaResponse:
    try:
        empresa = await svc.reativar(empresa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return EmpresaResponse.model_validate(empresa)
