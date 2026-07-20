import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentJti, CurrentUserId, RequireAdmin, RequireAdminOrGestor
from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.modules.usuario.repository import UsuarioRepository
from app.modules.usuario.schemas import (
    AlterarSenhaRequest,
    DefinirSenhaRequest,
    LoginRequest,
    RecuperarSenhaRequest,
    TokenResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.modules.usuario.service import AuthError, ContaBloqueadaError, UsuarioService

router_auth = APIRouter(prefix="/auth", tags=["auth"])
router_usuarios = APIRouter(prefix="/usuarios", tags=["usuarios"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> UsuarioService:
    return UsuarioService(UsuarioRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    if isinstance(exc, ContaBloqueadaError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    if isinstance(exc, AuthError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router_auth.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> TokenResponse:
    ip = request.client.host if request.client else None
    try:
        token = await svc.login(data, ip=ip)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TokenResponse(access_token=token)


@router_auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    jti: CurrentJti,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> None:
    if jti:
        await svc.logout(jti)


@router_auth.post("/recuperar-senha", status_code=status.HTTP_204_NO_CONTENT)
async def recuperar_senha(
    data: RecuperarSenhaRequest,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> None:
    await svc.recuperar_senha(str(data.email))


@router_auth.post("/definir-senha", status_code=status.HTTP_204_NO_CONTENT)
async def definir_senha(
    data: DefinirSenhaRequest,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> None:
    try:
        await svc.definir_senha(data)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router_usuarios.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UsuarioCreate,
    usuario_id: RequireAdminOrGestor,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.criar_usuario(data, criado_por=usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.get("/me", response_model=UsuarioResponse)
async def obter_usuario_atual(
    usuario_id: CurrentUserId,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.obter_usuario(usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.put("/me", response_model=UsuarioResponse)
async def atualizar_usuario_atual(
    data: UsuarioUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.atualizar_usuario(usuario_id, data)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.post("/me/alterar-senha", status_code=status.HTTP_204_NO_CONTENT)
async def alterar_senha(
    data: AlterarSenhaRequest,
    usuario_id: CurrentUserId,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> None:
    try:
        await svc.alterar_senha(usuario_id, data)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router_usuarios.get("", response_model=list[UsuarioResponse])
async def listar_usuarios(
    _: RequireAdminOrGestor,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> list[UsuarioResponse]:
    usuarios = await svc.listar_usuarios()
    return [UsuarioResponse.model_validate(u) for u in usuarios]


@router_usuarios.patch("/{usuario_id}/inativar", response_model=UsuarioResponse)
async def inativar_usuario(
    usuario_id: uuid.UUID,
    admin_id: RequireAdminOrGestor,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.inativar_usuario(usuario_id, admin_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.patch("/{usuario_id}/reativar", response_model=UsuarioResponse)
async def reativar_usuario(
    usuario_id: uuid.UUID,
    _: RequireAdminOrGestor,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.reativar_usuario(usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.patch("/{usuario_id}/gestor", response_model=UsuarioResponse)
async def toggle_gestor(
    usuario_id: uuid.UUID,
    admin_id: RequireAdmin,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.toggle_gestor(usuario_id, admin_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)


@router_usuarios.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(
    usuario_id: uuid.UUID,
    _admin: RequireAdminOrGestor,
    svc: Annotated[UsuarioService, Depends(_svc)],
) -> UsuarioResponse:
    try:
        usuario = await svc.obter_usuario(usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return UsuarioResponse.model_validate(usuario)
