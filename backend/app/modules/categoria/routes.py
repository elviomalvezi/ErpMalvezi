import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.categoria.repository import CategoriaRepository
from app.modules.categoria.schemas import (
    CategoriaCreate,
    CategoriaResponse,
    CategoriaTreeNode,
    CategoriaUpdate,
)
from app.modules.categoria.service import CategoriaService

router = APIRouter(prefix="/categorias", tags=["categorias"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> CategoriaService:
    return CategoriaService(CategoriaRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    from app.core.exceptions import ConflictError

    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[CategoriaResponse])
async def listar_categorias(
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    apenas_ativas: Annotated[bool, Query()] = True,
) -> list[CategoriaResponse]:
    categorias = await svc.listar(usuario_id, empresa_id, apenas_ativas)
    return [CategoriaResponse.model_validate(c) for c in categorias]


@router.get("/arvore", response_model=list[CategoriaTreeNode])
async def listar_arvore(
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[CategoriaTreeNode]:
    return await svc.listar_arvore(usuario_id, empresa_id)


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def criar_categoria(
    data: CategoriaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        cat = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(cat)


@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def obter_categoria(
    categoria_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        cat = await svc.obter(categoria_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(cat)


@router.put("/{categoria_id}", response_model=CategoriaResponse)
async def atualizar_categoria(
    categoria_id: uuid.UUID,
    data: CategoriaUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        cat = await svc.atualizar(categoria_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(cat)


@router.patch("/{categoria_id}/inativar", response_model=CategoriaResponse)
async def inativar_categoria(
    categoria_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        cat = await svc.inativar(categoria_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(cat)


@router.patch("/{categoria_id}/reativar", response_model=CategoriaResponse)
async def reativar_categoria(
    categoria_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        cat = await svc.reativar(categoria_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(cat)


@router.post("/{categoria_id}/merge/{destino_id}", response_model=CategoriaResponse)
async def merge_categorias(
    categoria_id: uuid.UUID,
    destino_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> CategoriaResponse:
    try:
        destino = await svc.merge(categoria_id, destino_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return CategoriaResponse.model_validate(destino)


@router.post("/plano-padrao", status_code=status.HTTP_201_CREATED)
async def inicializar_plano_padrao(
    usuario_id: CurrentUserId,
    svc: Annotated[CategoriaService, Depends(_svc)],
) -> dict[str, int]:
    try:
        total = await svc.inicializar_plano_padrao(usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return {"criadas": total}
