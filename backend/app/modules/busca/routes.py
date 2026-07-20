from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.categoria.models import Categoria
from app.modules.contato.models import Contato
from app.modules.empresa.models import UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento
from app.modules.lancamento.schemas import LancamentoResponse
from app.modules.contato.schemas import ContatoResponse

router = APIRouter(prefix="/busca", tags=["busca"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("")
async def busca_global(
    usuario_id: CurrentUserId,
    db: DbDep,
    q: Annotated[str, Query(min_length=2, max_length=100)] = "",
) -> dict:
    sq_emp = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)
    termo = f"%{q}%"

    # Lançamentos
    stmt_lanc = (
        select(Lancamento)
        .where(
            Lancamento.empresa_id.in_(sq_emp),
            Lancamento.ativo.is_(True),
            Lancamento.descricao.ilike(termo),
            Lancamento.status != StatusLancamento.CANCELADO,
        )
        .order_by(Lancamento.data_vencimento.desc())
        .limit(10)
    )
    res_lanc = await db.execute(stmt_lanc)
    lancamentos = [LancamentoResponse.model_validate(l) for l in res_lanc.scalars().all()]

    # Contatos
    stmt_cont = (
        select(Contato)
        .where(
            Contato.empresa_id.in_(sq_emp) | Contato.escopo.in_(["global"]),
            Contato.ativa.is_(True),
            Contato.nome_principal.ilike(termo),
        )
        .limit(5)
    )
    res_cont = await db.execute(stmt_cont)
    contatos = [ContatoResponse.model_validate(c) for c in res_cont.scalars().all()]

    # Categorias
    stmt_cat = (
        select(Categoria)
        .where(
            Categoria.ativa.is_(True),
            Categoria.nome.ilike(termo),
        )
        .limit(5)
    )
    res_cat = await db.execute(stmt_cat)
    cats = res_cat.scalars().all()
    categorias = [{"id": str(c.id), "nome": c.nome, "tipo": c.tipo} for c in cats]

    return {
        "lancamentos": lancamentos,
        "contatos": contatos,
        "categorias": categorias,
    }
