import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RequireAdmin
from app.core.exceptions import DomainError, NotFoundError
from app.modules.permissao.repository import PermissaoRepository
from app.modules.permissao.schemas import (
    AcaoResponse,
    ConcederPermissoesRequest,
    MenuResponse,
    PermissaoMatrizItem,
    UsuarioPermissoesResponse,
)
from app.modules.permissao.service import PermissaoService
from app.modules.usuario.repository import UsuarioRepository

router = APIRouter(prefix="/permissoes", tags=["permissoes"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> PermissaoService:
    return PermissaoService(PermissaoRepository(db), UsuarioRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("/menus", response_model=list[MenuResponse])
async def listar_menus(
    _: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> list[MenuResponse]:
    menus = await svc._repo.listar_menus()
    return [MenuResponse.model_validate(m) for m in menus]


@router.get("/acoes", response_model=list[AcaoResponse])
async def listar_acoes(
    _: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> list[AcaoResponse]:
    acoes = await svc._repo.listar_acoes()
    return [AcaoResponse.model_validate(a) for a in acoes]


@router.get("/usuarios/{usuario_id}", response_model=UsuarioPermissoesResponse)
async def listar_permissoes_usuario(
    usuario_id: uuid.UUID,
    _: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> UsuarioPermissoesResponse:
    try:
        return await svc.listar_permissoes_usuario(usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.post(
    "/usuarios/{usuario_id}",
    response_model=list[PermissaoMatrizItem],
    status_code=status.HTTP_201_CREATED,
)
async def conceder_permissoes(
    usuario_id: uuid.UUID,
    data: ConcederPermissoesRequest,
    admin_id: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> list[PermissaoMatrizItem]:
    try:
        return await svc.conceder_permissoes(usuario_id, data, admin_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.put("/usuarios/{usuario_id}", response_model=list[PermissaoMatrizItem])
async def substituir_permissoes(
    usuario_id: uuid.UUID,
    data: ConcederPermissoesRequest,
    admin_id: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> list[PermissaoMatrizItem]:
    try:
        return await svc.substituir_permissoes(usuario_id, data, admin_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.delete("/usuarios/{usuario_id}/{permissao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revogar_permissao(
    usuario_id: uuid.UUID,
    permissao_id: uuid.UUID,
    admin_id: RequireAdmin,
    svc: Annotated[PermissaoService, Depends(_svc)],
) -> None:
    try:
        await svc.revogar_permissao(permissao_id, admin_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
