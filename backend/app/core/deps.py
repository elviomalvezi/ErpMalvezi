import uuid
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


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


RequireAdmin = Annotated[uuid.UUID, Depends(_get_admin_user_id)]


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
