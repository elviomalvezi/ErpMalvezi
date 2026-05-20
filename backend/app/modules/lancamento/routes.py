import uuid
from datetime import date
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.core.storage import StorageProvider, get_storage_provider
from app.core.utils import new_uuid
from app.modules.categoria.repository import CategoriaRepository
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.contato.repository import ContatoRepository
from app.modules.empresa.repository import EmpresaRepository
from app.modules.fatura.repository import FaturaRepository
from app.modules.fatura.service import FaturaService
from app.modules.lancamento.importacao import (
    campos_obrigatorios,
    campos_suportados,
    ler_planilha,
    normalizar_linhas,
    validar_mapeamento,
)
from app.modules.lancamento.models import LancamentoAnexo, StatusLancamento, TipoLancamento
from app.modules.lancamento.repository import LancamentoRepository
from app.modules.lancamento.schemas import (
    LancamentoBaixaCreate,
    LancamentoAnexoResponse,
    ImportacaoAnaliseResponse,
    ImportacaoMapeamentoPayload,
    ImportacaoPreviewResponse,
    ImportacaoResultadoResponse,
    LancamentoCreate,
    LancamentoParceladoCreate,
    LancamentoRecorrenteCreate,
    LancamentoResponse,
    LancamentoUpdate,
)
from app.modules.lancamento.service import LancamentoService

router = APIRouter(prefix="/lancamentos", tags=["lancamentos"])

_MIME_PERMITIDOS = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv", "text/plain",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _svc(db: DbDep) -> LancamentoService:
    conta_repo = ContaBancariaRepository(db)
    fatura_repo = FaturaRepository(db)
    fatura_svc = FaturaService(fatura_repo, conta_repo)
    return LancamentoService(
        LancamentoRepository(db),
        conta_repo,
        fatura_svc,
        CategoriaRepository(db),
        ContatoRepository(db),
        EmpresaRepository(db),
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


@router.get("", response_model=list[LancamentoResponse])
async def listar_lancamentos(
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    tipo: Annotated[TipoLancamento | None, Query()] = None,
    status_lct: Annotated[StatusLancamento | None, Query(alias="status")] = None,
    data_inicio: Annotated[date | None, Query()] = None,
    data_fim: Annotated[date | None, Query()] = None,
    categoria_id: Annotated[uuid.UUID | None, Query()] = None,
    contato_id: Annotated[uuid.UUID | None, Query()] = None,
    conta_bancaria_id: Annotated[uuid.UUID | None, Query()] = None,
    grupo_parcelas_id: Annotated[uuid.UUID | None, Query()] = None,
    recorrencia_id: Annotated[uuid.UUID | None, Query()] = None,
    apenas_ativos: Annotated[bool, Query()] = True,
) -> list[LancamentoResponse]:
    lancamentos = await svc.listar(
        usuario_id,
        empresa_id=empresa_id,
        tipo=tipo,
        status=status_lct,
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria_id=categoria_id,
        contato_id=contato_id,
        conta_bancaria_id=conta_bancaria_id,
        grupo_parcelas_id=grupo_parcelas_id,
        recorrencia_id=recorrencia_id,
        apenas_ativos=apenas_ativos,
    )
    return [LancamentoResponse.model_validate(lct) for lct in lancamentos]


@router.post("", response_model=LancamentoResponse, status_code=status.HTTP_201_CREATED)
async def criar_lancamento(
    data: LancamentoCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.criar_simples(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.post(
    "/parcelado",
    response_model=list[LancamentoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def criar_lancamento_parcelado(
    data: LancamentoParceladoCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> list[LancamentoResponse]:
    try:
        lancamentos = await svc.criar_parcelado(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return [LancamentoResponse.model_validate(lct) for lct in lancamentos]


@router.post(
    "/recorrente",
    response_model=list[LancamentoResponse],
    status_code=status.HTTP_201_CREATED,
)
async def criar_lancamento_recorrente(
    data: LancamentoRecorrenteCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> list[LancamentoResponse]:
    try:
        lancamentos = await svc.criar_recorrente(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return [LancamentoResponse.model_validate(lct) for lct in lancamentos]


@router.get("/{lancamento_id}", response_model=LancamentoResponse)
async def obter_lancamento(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.obter(lancamento_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.put("/{lancamento_id}", response_model=LancamentoResponse)
async def atualizar_lancamento(
    lancamento_id: uuid.UUID,
    data: LancamentoUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.atualizar(lancamento_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.post("/{lancamento_id}/baixa", response_model=LancamentoResponse)
async def registrar_baixa(
    lancamento_id: uuid.UUID,
    data: LancamentoBaixaCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.registrar_baixa(lancamento_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.patch("/{lancamento_id}/cancelar", response_model=LancamentoResponse)
async def cancelar_lancamento(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.cancelar(lancamento_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.post("/importacao/analisar", response_model=ImportacaoAnaliseResponse)
async def analisar_importacao(
    usuario_id: CurrentUserId,
    file: Annotated[UploadFile, File(description="Planilha CSV ou XLSX")],
) -> ImportacaoAnaliseResponse:
    nome = file.filename or "planilha"
    conteudo = await file.read()
    try:
        arquivo = ler_planilha(nome, conteudo)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoAnaliseResponse(
        colunas=arquivo.colunas,
        total_linhas=len(arquivo.linhas),
        amostras=arquivo.linhas[:5],
        campos_suportados=sorted(campos_suportados()),
        campos_obrigatorios=sorted(campos_obrigatorios()),
    )


@router.post("/importacao/pre-visualizar", response_model=ImportacaoPreviewResponse)
async def pre_visualizar_importacao(
    usuario_id: CurrentUserId,
    empresa_id: Annotated[uuid.UUID, Form()],
    tipo: Annotated[TipoLancamento | None, Form()] = None,
    mapeamento_json: Annotated[str, Form()] = "{}",
    file: Annotated[UploadFile, File(description="Planilha CSV ou XLSX")] = ...,
    svc: Annotated[LancamentoService, Depends(_svc)] = ...,
) -> ImportacaoPreviewResponse:
    _ = (usuario_id, empresa_id, tipo, svc)
    nome = file.filename or "planilha"
    conteudo = await file.read()
    try:
        arquivo = ler_planilha(nome, conteudo)
        mapeamento = validar_mapeamento(_parse_mapeamento(mapeamento_json))
        itens = normalizar_linhas(arquivo, mapeamento)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoPreviewResponse(
        total_linhas=len(itens),
        linhas_validas=sum(1 for item in itens if item["valida"]),
        linhas_invalidas=sum(1 for item in itens if not item["valida"]),
        itens=itens[:200],
    )


@router.post("/importacao/confirmar", response_model=ImportacaoResultadoResponse)
async def confirmar_importacao(
    usuario_id: CurrentUserId,
    empresa_id: Annotated[uuid.UUID, Form()],
    tipo: Annotated[TipoLancamento | None, Form()] = None,
    mapeamento_json: Annotated[str, Form()] = "{}",
    file: Annotated[UploadFile, File(description="Planilha CSV ou XLSX")] = ...,
    svc: Annotated[LancamentoService, Depends(_svc)] = ...,
) -> ImportacaoResultadoResponse:
    nome = file.filename or "planilha"
    conteudo = await file.read()
    try:
        arquivo = ler_planilha(nome, conteudo)
        mapeamento = validar_mapeamento(_parse_mapeamento(mapeamento_json))
        itens = normalizar_linhas(arquivo, mapeamento)
        importadas = await svc.importar_linhas(empresa_id, tipo, itens, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoResultadoResponse(
        total_linhas=len(itens),
        importadas=importadas,
        ignoradas=len(itens) - importadas,
    )


# ── Anexos ────────────────────────────────────────────────────────────────────

async def _get_lancamento_ou_404(lancamento_id: uuid.UUID, usuario_id: uuid.UUID, db: AsyncSession) -> None:
    from app.modules.lancamento.models import Lancamento as LancamentoModel
    result = await db.execute(
        select(LancamentoModel).where(
            LancamentoModel.id == lancamento_id,
            LancamentoModel.usuario_id == usuario_id,
            LancamentoModel.ativo.is_(True),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lançamento não encontrado.")


@router.get("/{lancamento_id}/anexos", response_model=list[LancamentoAnexoResponse])
async def listar_anexos(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> list[LancamentoAnexoResponse]:
    await _get_lancamento_ou_404(lancamento_id, usuario_id, db)
    result = await db.execute(
        select(LancamentoAnexo).where(
            LancamentoAnexo.lancamento_id == lancamento_id,
            LancamentoAnexo.ativo.is_(True),
        ).order_by(LancamentoAnexo.criado_em)
    )
    return [LancamentoAnexoResponse.model_validate(a) for a in result.scalars().all()]


@router.post(
    "/{lancamento_id}/anexos",
    response_model=LancamentoAnexoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_anexo(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
    file: Annotated[UploadFile, File(description="Arquivo a anexar (máx. 10 MB)")],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> LancamentoAnexoResponse:
    await _get_lancamento_ou_404(lancamento_id, usuario_id, db)

    conteudo = await file.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo excede 10 MB.")

    mime = file.content_type or "application/octet-stream"
    if mime not in _MIME_PERMITIDOS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Tipo de arquivo não permitido: {mime}")

    nome_original = file.filename or "arquivo"
    ext = nome_original.rsplit(".", 1)[-1] if "." in nome_original else "bin"
    caminho = f"anexos/{lancamento_id}/{new_uuid()}.{ext}"
    await storage.salvar(conteudo, caminho, mime)

    anexo = LancamentoAnexo(
        id=new_uuid(),
        lancamento_id=lancamento_id,
        usuario_id=usuario_id,
        nome_original=nome_original,
        tamanho=len(conteudo),
        mime_type=mime,
        caminho=caminho,
    )
    db.add(anexo)
    await db.commit()
    await db.refresh(anexo)
    return LancamentoAnexoResponse.model_validate(anexo)


@router.delete("/{lancamento_id}/anexos/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_anexo(
    lancamento_id: uuid.UUID,
    anexo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> None:
    await _get_lancamento_ou_404(lancamento_id, usuario_id, db)
    result = await db.execute(
        select(LancamentoAnexo).where(
            LancamentoAnexo.id == anexo_id,
            LancamentoAnexo.lancamento_id == lancamento_id,
            LancamentoAnexo.ativo.is_(True),
        )
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado.")

    await storage.excluir(anexo.caminho)
    anexo.ativo = False
    await db.commit()


@router.get("/{lancamento_id}/anexos/{anexo_id}/download")
async def download_anexo(
    lancamento_id: uuid.UUID,
    anexo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> Response:
    await _get_lancamento_ou_404(lancamento_id, usuario_id, db)
    result = await db.execute(
        select(LancamentoAnexo).where(
            LancamentoAnexo.id == anexo_id,
            LancamentoAnexo.lancamento_id == lancamento_id,
            LancamentoAnexo.ativo.is_(True),
        )
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado.")

    try:
        conteudo = await storage.ler(anexo.caminho)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no storage.")

    return Response(
        content=conteudo,
        media_type=anexo.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{anexo.nome_original}"'},
    )


def _parse_mapeamento(mapeamento_json: str) -> dict[str, str | None]:
    try:
        payload = json.loads(mapeamento_json)
        if not isinstance(payload, dict):
            raise ValueError
        return ImportacaoMapeamentoPayload.model_validate(payload).model_dump()
    except (ValueError, json.JSONDecodeError) as exc:
        raise DomainError("Mapeamento da importação inválido.") from exc
