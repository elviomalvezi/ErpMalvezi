import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.conciliacao.models import StatusTransacao
from app.modules.conciliacao.repository import ConciliacaoRepository
from app.modules.conciliacao.schemas import (
    ConciliarRequest,
    ConfigCSV,
    CriarLancamentoRequest,
    ImportacaoResponse,
    RegraCategorizacaoResponse,
    SugestaoMatchResponse,
    TransacaoBancariaResponse,
)
from app.modules.conciliacao.service import ConciliacaoService
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.lancamento.repository import LancamentoRepository

router = APIRouter(prefix="/conciliacao", tags=["conciliacao"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> ConciliacaoService:
    return ConciliacaoService(
        ConciliacaoRepository(db),
        ContaBancariaRepository(db),
        LancamentoRepository(db),
    )


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.post("/importar/ofx", response_model=ImportacaoResponse, status_code=status.HTTP_201_CREATED)
async def importar_ofx(
    arquivo: UploadFile,
    conta_bancaria_id: Annotated[uuid.UUID, Query()],
    empresa_id: Annotated[uuid.UUID, Query()],
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> ImportacaoResponse:
    content = await arquivo.read()
    nome = arquivo.filename or "extrato.ofx"
    try:
        importacao = await svc.importar_ofx(content, nome, conta_bancaria_id, empresa_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoResponse.model_validate(importacao)


@router.post("/importar/csv", response_model=ImportacaoResponse, status_code=status.HTTP_201_CREATED)
async def importar_csv(
    arquivo: UploadFile,
    conta_bancaria_id: Annotated[uuid.UUID, Query()],
    empresa_id: Annotated[uuid.UUID, Query()],
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
    config: Annotated[ConfigCSV, Depends(ConfigCSV)],
) -> ImportacaoResponse:
    content = await arquivo.read()
    nome = arquivo.filename or "extrato.csv"
    try:
        importacao = await svc.importar_csv(content, nome, conta_bancaria_id, empresa_id, usuario_id, config)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoResponse.model_validate(importacao)


@router.get("/importacoes", response_model=list[ImportacaoResponse])
async def listar_importacoes(
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
    conta_bancaria_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[ImportacaoResponse]:
    importacoes = await svc.listar_importacoes(usuario_id, conta_bancaria_id)
    return [ImportacaoResponse.model_validate(i) for i in importacoes]


@router.get("/importacoes/{importacao_id}/transacoes", response_model=list[TransacaoBancariaResponse])
async def listar_transacoes(
    importacao_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
    status_transacao: Annotated[StatusTransacao | None, Query(alias="status")] = None,
) -> list[TransacaoBancariaResponse]:
    try:
        transacoes = await svc.listar_transacoes(importacao_id, usuario_id, status_transacao)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return [TransacaoBancariaResponse.model_validate(t) for t in transacoes]


@router.get("/transacoes/{transacao_id}/sugerir-match", response_model=list[SugestaoMatchResponse])
async def sugerir_match(
    transacao_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> list[SugestaoMatchResponse]:
    try:
        lancamentos = await svc.sugerir_match(transacao_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return [SugestaoMatchResponse.model_validate(lct) for lct in lancamentos]


@router.post("/transacoes/{transacao_id}/conciliar", response_model=TransacaoBancariaResponse)
async def conciliar(
    transacao_id: uuid.UUID,
    body: ConciliarRequest,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> TransacaoBancariaResponse:
    try:
        transacao = await svc.conciliar(transacao_id, body.lancamento_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransacaoBancariaResponse.model_validate(transacao)


@router.post(
    "/transacoes/{transacao_id}/criar-lancamento",
    response_model=TransacaoBancariaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_lancamento(
    transacao_id: uuid.UUID,
    body: CriarLancamentoRequest,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> TransacaoBancariaResponse:
    try:
        transacao = await svc.criar_lancamento_de_transacao(transacao_id, body, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransacaoBancariaResponse.model_validate(transacao)


@router.patch("/transacoes/{transacao_id}/ignorar", response_model=TransacaoBancariaResponse)
async def ignorar(
    transacao_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> TransacaoBancariaResponse:
    try:
        transacao = await svc.ignorar(transacao_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return TransacaoBancariaResponse.model_validate(transacao)


@router.get("/transacoes/{transacao_id}/sugerir-categoria", response_model=RegraCategorizacaoResponse | None)
async def sugerir_categoria(
    transacao_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[ConciliacaoService, Depends(_svc)],
) -> RegraCategorizacaoResponse | None:
    try:
        regra = await svc.sugerir_categoria(transacao_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    if regra is None:
        return None
    return RegraCategorizacaoResponse.model_validate(regra)
