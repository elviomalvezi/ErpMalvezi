import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.fluxo_caixa.repository import FluxoCaixaRepository
from app.modules.fluxo_caixa.schemas import FluxoCaixaResponse
from app.modules.fluxo_caixa.service import FluxoCaixaService

router = APIRouter(prefix="/fluxo-caixa", tags=["fluxo-caixa"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> FluxoCaixaService:
    return FluxoCaixaService(FluxoCaixaRepository(db))


@router.get("", response_model=FluxoCaixaResponse)
async def obter_fluxo_caixa(
    usuario_id: CurrentUserId,
    svc: Annotated[FluxoCaixaService, Depends(_svc)],
    data_inicio: Annotated[date, Query()],
    data_fim: Annotated[date, Query()],
    empresa_ids: Annotated[list[uuid.UUID], Query()] = [],
    conta_bancaria_id: Annotated[uuid.UUID | None, Query()] = None,
) -> FluxoCaixaResponse:
    return await svc.obter(usuario_id, data_inicio, data_fim, empresa_ids or None, conta_bancaria_id)
