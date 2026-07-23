import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.lancamento.models import TipoLancamento
from app.modules.relatorio.repository import RelatorioRepository
from app.modules.relatorio.schemas import DreLinha, DreResponse

router = APIRouter(prefix="/relatorios", tags=["relatorios"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/dre", response_model=DreResponse)
async def dre(
    usuario_id: CurrentUserId,
    db: DbDep,
    mes_referencia: Annotated[str, Query(description="Mês no formato YYYY-MM")] = "",
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
) -> DreResponse:
    repo = RelatorioRepository(db)

    hoje = date.today()
    if mes_referencia:
        ano, mes = int(mes_referencia[:4]), int(mes_referencia[5:7])
    else:
        ano, mes = hoje.year, hoje.month

    if mes == 1:
        ano_ant, mes_ant = ano - 1, 12
    else:
        ano_ant, mes_ant = ano, mes - 1

    import calendar

    def _periodo(y: int, m: int) -> tuple[date, date]:
        ultimo = calendar.monthrange(y, m)[1]
        return date(y, m, 1), date(y, m, ultimo)

    inicio_atual, fim_atual = _periodo(ano, mes)
    inicio_ant, fim_ant = _periodo(ano_ant, mes_ant)

    rec_atual_rows = await repo.dre_por_categoria(
        usuario_id, inicio_atual, fim_atual, TipoLancamento.RECEITA, empresa_id
    )
    rec_ant_rows = await repo.dre_por_categoria(
        usuario_id, inicio_ant, fim_ant, TipoLancamento.RECEITA, empresa_id
    )
    desp_atual_rows = await repo.dre_por_categoria(
        usuario_id, inicio_atual, fim_atual, TipoLancamento.DESPESA, empresa_id
    )
    desp_ant_rows = await repo.dre_por_categoria(
        usuario_id, inicio_ant, fim_ant, TipoLancamento.DESPESA, empresa_id
    )

    def _merge(atual: list[dict], anterior: list[dict]) -> list[DreLinha]:
        ant_map = {r["categoria_id"]: r["total"] for r in anterior}
        linhas = []
        for r in atual:
            total_ant = ant_map.get(r["categoria_id"]) or anterior_total_from_rows(anterior, r["categoria_id"])
            variacao = None
            if total_ant and total_ant != 0:
                variacao = float((r["total"] - total_ant) / total_ant * 100)
            linhas.append(
                DreLinha(
                    categoria_id=r["categoria_id"],
                    categoria_nome=r["categoria_nome"],
                    nivel=r["nivel"],
                    parent_id=r["parent_id"],
                    total_atual=r["total"],
                    total_anterior=total_ant or 0,
                    variacao_pct=variacao,
                )
            )
        return linhas

    def anterior_total_from_rows(rows: list[dict], cat_id: str) -> float:
        for r in rows:
            if r["categoria_id"] == cat_id:
                return float(r["total"])
        return 0.0

    receitas = _merge(rec_atual_rows, rec_ant_rows)
    despesas = _merge(desp_atual_rows, desp_ant_rows)

    from decimal import Decimal

    tot_rec_atual = sum((r.total_atual for r in receitas), Decimal(0))
    tot_rec_ant = sum((r.total_anterior for r in receitas), Decimal(0))
    tot_desp_atual = sum((r.total_atual for r in despesas), Decimal(0))
    tot_desp_ant = sum((r.total_anterior for r in despesas), Decimal(0))

    empresa_nome: str | None = None
    if empresa_id:
        empresa_nome = await repo.nome_empresa(empresa_id, usuario_id)

    return DreResponse(
        mes_referencia=f"{ano:04d}-{mes:02d}",
        mes_anterior=f"{ano_ant:04d}-{mes_ant:02d}",
        empresa_nome=empresa_nome,
        receitas=receitas,
        total_receitas_atual=tot_rec_atual,
        total_receitas_anterior=tot_rec_ant,
        despesas=despesas,
        total_despesas_atual=tot_desp_atual,
        total_despesas_anterior=tot_desp_ant,
        resultado_atual=tot_rec_atual - tot_desp_atual,
        resultado_anterior=tot_rec_ant - tot_desp_ant,
    )
