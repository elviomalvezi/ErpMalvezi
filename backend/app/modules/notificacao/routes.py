from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.notificacao.service import NotificacaoService

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("/enviar-vencimentos")
async def enviar_notificacoes(
    _usuario_id: CurrentUserId,
    db: DbDep,
) -> dict:
    """Envia e-mails de alerta de vencimentos manualmente. Requer autenticação."""
    enviados = await NotificacaoService(db).enviar_vencimentos()
    return {"enviados": enviados, "mensagem": f"{enviados} e-mail(is) enviado(s)."}
