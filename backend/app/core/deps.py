import uuid
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auditoria import set_usuario_auditoria
from app.core.database import get_db
from app.core.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("sub") is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return payload
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc


async def get_current_user_id(
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
    db: DbDep,
) -> uuid.UUID:
    from sqlalchemy import select

    from app.modules.usuario.models import Usuario

    usuario_id = uuid.UUID(payload["sub"])

    # Revogação de token: confere se o usuário está ativo e se a versão do token
    # bate com a atual. Inativar usuário ou trocar senha incrementa token_version,
    # invalidando na hora todos os tokens já emitidos.
    row = (
        await db.execute(
            select(Usuario.ativo, Usuario.token_version).where(Usuario.id == usuario_id)
        )
    ).one_or_none()
    if row is None or not row.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou usuário inativo.",
        )
    if int(payload.get("tv", -1)) != int(row.token_version):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão encerrada. Faça login novamente.",
        )

    # Marca o usuário da requisição para a auditoria automática (before_flush).
    set_usuario_auditoria(usuario_id)
    return usuario_id


async def get_current_jti(
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
) -> str | None:
    return payload.get("jti")


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
CurrentJti = Annotated[str | None, Depends(get_current_jti)]


async def _get_admin_user_id(
    usuario_id: CurrentUserId,
    db: DbDep,
) -> uuid.UUID:
    from sqlalchemy import select

    from app.modules.usuario.models import Usuario

    result = await db.execute(select(Usuario.admin).where(Usuario.id == usuario_id))
    is_admin = result.scalar_one_or_none()
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores."
        )
    return usuario_id


async def _get_admin_or_gestor_id(
    usuario_id: CurrentUserId,
    db: DbDep,
) -> uuid.UUID:
    from sqlalchemy import select

    from app.modules.usuario.models import Usuario

    result = await db.execute(
        select(Usuario.admin, Usuario.gestor).where(Usuario.id == usuario_id)
    )
    row = result.one_or_none()
    if row is None or (not row.admin and not row.gestor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores e gestores.",
        )
    return usuario_id


RequireAdmin = Annotated[uuid.UUID, Depends(_get_admin_user_id)]
RequireAdminOrGestor = Annotated[uuid.UUID, Depends(_get_admin_or_gestor_id)]


def require_permissao(menu_chave: str, acao_chave: str) -> Any:
    """Factory que retorna um Depends verificando se o usuário tem a permissão solicitada."""

    async def _check(usuario_id: CurrentUserId, db: DbDep) -> uuid.UUID:
        from app.modules.permissao.repository import PermissaoRepository

        repo = PermissaoRepository(db)
        allowed = await repo.verificar_permissao(usuario_id, menu_chave, acao_chave)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem permissão: {menu_chave}.{acao_chave}",
            )
        return usuario_id

    return Depends(_check)
