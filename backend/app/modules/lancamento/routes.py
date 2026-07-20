import uuid
from datetime import date
import json
from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile, status
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
    ExtratoResponse,
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

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB (anexos)
_MAX_IMPORT_BYTES = 25 * 1024 * 1024  # 25 MB (planilhas de importação)

# MIME permitido → (extensão canônica, assinaturas/magic bytes aceitas).
# A extensão guardada é derivada DAQUI (não do nome enviado pelo cliente),
# eliminando path traversal via filename. O conteúdo é validado pelos magic
# bytes — o content-type do cliente não é confiável sozinho.
# Tupla de assinaturas vazia => tipo textual (validado por ausência de bytes nulos).
_TIPOS_PERMITIDOS: dict[str, tuple[str, tuple[bytes, ...]]] = {
    "application/pdf": ("pdf", (b"%PDF",)),
    "image/jpeg": ("jpg", (b"\xff\xd8\xff",)),
    "image/png": ("png", (b"\x89PNG\r\n\x1a\n",)),
    "image/gif": ("gif", (b"GIF87a", b"GIF89a")),
    "image/webp": ("webp", (b"RIFF",)),  # "WEBP" no offset 8 checado à parte
    "application/msword": ("doc", (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)),
    "application/vnd.ms-excel": ("xls", (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("docx", (b"PK\x03\x04",)),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("xlsx", (b"PK\x03\x04",)),
    "text/csv": ("csv", ()),
    "text/plain": ("txt", ()),
}


def _sanitizar_nome(nome: str) -> str:
    """Remove separadores de caminho, aspas e caracteres de controle.

    Evita header injection no Content-Disposition e path traversal via nome.
    """
    nome = nome.replace("\\", "/").rsplit("/", 1)[-1]
    nome = "".join(c for c in nome if c.isprintable() and c not in '"\r\n')
    nome = nome.strip() or "arquivo"
    return nome[:200]


def _validar_conteudo(mime: str, conteudo: bytes) -> str:
    """Valida o MIME declarado contra os magic bytes reais; retorna a extensão canônica.

    Levanta HTTPException 415 se o tipo não for permitido ou o conteúdo não casar.
    """
    if mime not in _TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo não permitido: {mime}",
        )
    ext, assinaturas = _TIPOS_PERMITIDOS[mime]
    if not assinaturas:
        # Tipo textual: rejeita se houver bytes nulos (indício de binário disfarçado).
        if b"\x00" in conteudo[:8192]:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Conteúdo não corresponde a um arquivo de texto.",
            )
        return ext
    if not any(conteudo.startswith(sig) for sig in assinaturas):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="O conteúdo do arquivo não corresponde ao tipo informado.",
        )
    # WebP: "RIFF....WEBP" — confirma o marcador no offset 8.
    if mime == "image/webp" and conteudo[8:12] != b"WEBP":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="O conteúdo do arquivo não corresponde ao tipo informado.",
        )
    return ext


async def _ler_limitado(file: UploadFile, limite: int) -> bytes:
    """Lê o upload em blocos, abortando em 413 assim que ultrapassa `limite`.

    Evita carregar arquivos gigantes inteiros em memória antes de checar o tamanho.
    """
    partes: list[bytes] = []
    total = 0
    while True:
        bloco = await file.read(64 * 1024)
        if not bloco:
            break
        total += len(bloco)
        if total > limite:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede 10 MB.",
            )
        partes.append(bloco)
    return b"".join(partes)

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
    db: DbDep,
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
    descricao: Annotated[str | None, Query(min_length=2)] = None,
    limit: Annotated[int | None, Query(ge=1, le=200)] = None,
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
        descricao=descricao,
        limit=limit,
    )
    if not lancamentos:
        return []
    ids = [lct.id for lct in lancamentos]
    res_anexos = await db.execute(
        select(LancamentoAnexo.lancamento_id)
        .where(LancamentoAnexo.lancamento_id.in_(ids), LancamentoAnexo.ativo.is_(True))
        .distinct()
    )
    ids_com_anexo: set[uuid.UUID] = set(res_anexos.scalars().all())
    return [
        LancamentoResponse.model_validate(lct).model_copy(update={"tem_anexo": lct.id in ids_com_anexo})
        for lct in lancamentos
    ]


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


@router.get("/extrato", response_model=ExtratoResponse)
async def extrato_bancario(
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
    conta_bancaria_id: Annotated[uuid.UUID, Query()],
    data_inicio: Annotated[date | None, Query()] = None,
    data_fim: Annotated[date | None, Query()] = None,
) -> ExtratoResponse:
    try:
        return await svc.extrato(conta_bancaria_id, usuario_id, data_inicio, data_fim)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


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


@router.patch("/{lancamento_id}/nao-realizado", response_model=LancamentoResponse)
async def marcar_nao_realizado(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.marcar_nao_realizado(lancamento_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.patch("/{lancamento_id}/reverter-previsto", response_model=LancamentoResponse)
async def reverter_para_previsto(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
) -> LancamentoResponse:
    try:
        lct = await svc.reverter_para_previsto(lancamento_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.post("/{lancamento_id}/duplicar", response_model=LancamentoResponse, status_code=status.HTTP_201_CREATED)
async def duplicar_lancamento(
    lancamento_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[LancamentoService, Depends(_svc)],
    empresa_id: Annotated[uuid.UUID | None, Body(embed=True)] = None,
) -> LancamentoResponse:
    try:
        lct = await svc.duplicar(lancamento_id, usuario_id, empresa_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return LancamentoResponse.model_validate(lct)


@router.post("/importacao/analisar", response_model=ImportacaoAnaliseResponse)
async def analisar_importacao(
    usuario_id: CurrentUserId,
    file: Annotated[UploadFile, File(description="Planilha CSV ou XLSX")],
) -> ImportacaoAnaliseResponse:
    nome = file.filename or "planilha"
    conteudo = await _ler_limitado(file, _MAX_IMPORT_BYTES)
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
    conteudo = await _ler_limitado(file, _MAX_IMPORT_BYTES)
    try:
        arquivo = ler_planilha(nome, conteudo)
        mapeamento = validar_mapeamento(_parse_mapeamento(mapeamento_json))
        mapeamento = _auto_mapear(mapeamento, arquivo.colunas)
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
    import structlog as _sl
    _log = _sl.get_logger()
    nome = file.filename or "planilha"
    conteudo = await _ler_limitado(file, _MAX_IMPORT_BYTES)
    try:
        arquivo = ler_planilha(nome, conteudo)
        mapeamento = validar_mapeamento(_parse_mapeamento(mapeamento_json))
        mapeamento = _auto_mapear(mapeamento, arquivo.colunas)
        _log.info("importacao_mapeamento_final", mapeamento=mapeamento, colunas=arquivo.colunas[:20])
        itens = normalizar_linhas(arquivo, mapeamento)
        importadas, empresas_criadas = await svc.importar_linhas(empresa_id, tipo, itens, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return ImportacaoResultadoResponse(
        total_linhas=len(itens),
        importadas=importadas,
        ignoradas=len(itens) - importadas,
        empresas_criadas_importacao=empresas_criadas,
    )


# ── Anexos ────────────────────────────────────────────────────────────────────

async def _get_lancamento_ou_404(lancamento_id: uuid.UUID, usuario_id: uuid.UUID, db: AsyncSession) -> None:
    from app.modules.empresa.models import UsuarioEmpresa
    from app.modules.lancamento.models import Lancamento as LancamentoModel
    sq_empresas = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)
    result = await db.execute(
        select(LancamentoModel).where(
            LancamentoModel.id == lancamento_id,
            LancamentoModel.empresa_id.in_(sq_empresas),
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
) -> LancamentoAnexoResponse:
    await _get_lancamento_ou_404(lancamento_id, usuario_id, db)

    conteudo = await _ler_limitado(file, _MAX_BYTES)
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Arquivo vazio.")

    mime = file.content_type or "application/octet-stream"
    # Valida magic bytes (a extensão derivada confirma o tipo, mas não é usada
    # para caminho já que o conteúdo é gravado no próprio banco).
    _validar_conteudo(mime, conteudo)

    nome_original = _sanitizar_nome(file.filename or "arquivo")

    anexo = LancamentoAnexo(
        id=new_uuid(),
        lancamento_id=lancamento_id,
        usuario_id=usuario_id,
        nome_original=nome_original,
        tamanho=len(conteudo),
        mime_type=mime,
        # Conteúdo no banco (BYTEA); `caminho` fica nulo (storage em disco é legado).
        conteudo=conteudo,
        caminho=None,
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

    # Conteúdo no banco é removido pelo soft delete; só limpa disco se for legado.
    if anexo.caminho:
        await storage.excluir(anexo.caminho)
    anexo.ativo = False
    await db.commit()


@router.get("/{lancamento_id}/anexos/{anexo_id}/view")
async def ver_anexo(
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
    conteudo = anexo.conteudo
    if conteudo is None:
        # Registro legado: conteúdo ainda em disco. Lê via storage como fallback.
        if not anexo.caminho:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no storage.")
        try:
            conteudo = await storage.ler(anexo.caminho)
        except (FileNotFoundError, PermissionError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no storage.")
    # Só exibe inline tipos seguros para o navegador renderizar (imagem/PDF).
    # Demais tipos vão como anexo, evitando execução de conteúdo no contexto da origem.
    inline = anexo.mime_type in {"application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp"}
    disposicao = "inline" if inline else "attachment"
    nome = _sanitizar_nome(anexo.nome_original)
    return Response(
        content=conteudo,
        media_type=anexo.mime_type,
        headers={
            "Content-Disposition": f'{disposicao}; filename="{nome}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


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

    conteudo = anexo.conteudo
    if conteudo is None:
        # Registro legado: conteúdo ainda em disco. Lê via storage como fallback.
        if not anexo.caminho:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no storage.")
        try:
            conteudo = await storage.ler(anexo.caminho)
        except (FileNotFoundError, PermissionError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no storage.")

    nome = _sanitizar_nome(anexo.nome_original)
    return Response(
        content=conteudo,
        media_type=anexo.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nome}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


def _parse_mapeamento(mapeamento_json: str) -> dict[str, str | None]:
    try:
        payload = json.loads(mapeamento_json)
        if not isinstance(payload, dict):
            raise ValueError
        return ImportacaoMapeamentoPayload.model_validate(payload).model_dump()
    except (ValueError, json.JSONDecodeError) as exc:
        raise DomainError("Mapeamento da importação inválido.") from exc


def _auto_mapear(mapeamento: dict[str, str], colunas: list[str]) -> dict[str, str]:
    """Preenche campos opcionais não mapeados detectando colunas automaticamente."""
    import unicodedata

    def norm(s: str) -> str:
        s = s.lower().strip()
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return "".join(c for c in s if c.isalnum())

    _ALIASES: dict[str, list[str]] = {
        "col_tipo":       ["capcar", "cap/car", "receitas/despesas", "receitasdespesas", "receitas/despes", "tipo", "natureza", "tipomovimento"],
        "col_empresa":    ["titular", "empresa", "empresatitular", "entidade", "razaosocial"],
        "contato_nome":   ["fornecedor/cliente", "fornecedorcliente", "fornecedor", "cliente", "contato", "favorecido", "beneficiario", "pagador"],
        "categoria_nome": ["categoria", "category", "classificacao", "planocontas"],
        "conta_banco":    ["banco", "bancoinstituicao", "instituicao"],
        "conta_agencia":  ["agencia", "agenciabancaria", "numagencia"],
        "conta_numero":   ["conta", "contacorrente", "numeroconta", "numconta"],
        "observacoes":    ["observacoes", "obs", "notas", "complemento", "detalhe"],
    }

    resultado = dict(mapeamento)
    col_norm = {norm(c): c for c in colunas}

    for campo, aliases in _ALIASES.items():
        if resultado.get(campo):
            continue  # já mapeado pelo usuário
        for alias in aliases:
            # match exato
            if alias in col_norm:
                resultado[campo] = col_norm[alias]
                break
            # match parcial (coluna contém alias ou alias contém coluna)
            match = next(
                (orig for n, orig in col_norm.items() if len(n) > 2 and len(alias) > 2 and (n in alias or alias in n)),
                None,
            )
            if match:
                resultado[campo] = match
                break

    return resultado
