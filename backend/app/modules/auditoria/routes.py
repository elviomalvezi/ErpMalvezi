import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.modules.auditoria.models import Auditoria

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/lancamento/{lancamento_id}")
async def historico_lancamento(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> list[dict]:
    from app.modules.empresa.models import UsuarioEmpresa
    from app.modules.lancamento.models import Lancamento

    # Só permite ver o histórico de lançamentos de empresas que o usuário acessa.
    sq_empresas = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)
    acesso = await db.execute(
        select(Lancamento.id).where(
            Lancamento.id == lancamento_id,
            Lancamento.empresa_id.in_(sq_empresas),
        )
    )
    if acesso.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lançamento não encontrado.")

    result = await db.execute(
        select(Auditoria)
        .where(Auditoria.tabela == "lancamento", Auditoria.registro_id == lancamento_id)
        .order_by(Auditoria.criado_em.desc())
        .limit(50)
    )
    registros = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "acao": r.acao,
            "usuario_id": str(r.usuario_id) if r.usuario_id else None,
            "valor_anterior": r.valor_anterior,
            "valor_novo": r.valor_novo,
            "criado_em": r.criado_em.isoformat(),
        }
        for r in registros
    ]
