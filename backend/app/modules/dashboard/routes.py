import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import DashboardResponse, GraficosResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> DashboardService:
    return DashboardService(DashboardRepository(db))


@router.get("", response_model=DashboardResponse)
async def obter_dashboard(
    usuario_id: CurrentUserId,
    svc: Annotated[DashboardService, Depends(_svc)],
    data_inicio: Annotated[date, Query()],
    data_fim: Annotated[date, Query()],
    data_referencia: Annotated[date, Query()],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
) -> DashboardResponse:
    return await svc.obter(usuario_id, data_inicio, data_fim, data_referencia, empresa_id)


@router.get("/graficos", response_model=GraficosResponse)
async def obter_graficos(
    usuario_id: CurrentUserId,
    svc: Annotated[DashboardService, Depends(_svc)],
    data_inicio: Annotated[date, Query()],
    data_fim: Annotated[date, Query()],
    data_referencia: Annotated[date, Query()],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
) -> GraficosResponse:
    return await svc.graficos(usuario_id, data_inicio, data_fim, data_referencia, empresa_id)
