import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.modules.certificado.models import TipoCertificado
from app.modules.certificado.repository import CertificadoRepository
from app.modules.certificado.schemas import (
    CertificadoManualCreate,
    CertificadoResponse,
    CertificadoResumo,
    CertificadoUpdate,
)
from app.modules.certificado.service import CertificadoService

router = APIRouter(prefix="/certificados", tags=["certificados"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB (certificados são pequenos)


def _svc(db: DbDep) -> CertificadoService:
    return CertificadoService(CertificadoRepository(db))


def _handle_domain(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("", response_model=list[CertificadoResponse])
async def listar_certificados(
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
    tipo: Annotated[TipoCertificado | None, Query()] = None,
    apenas_ativos: Annotated[bool, Query()] = True,
) -> list[CertificadoResponse]:
    return await svc.listar(usuario_id, tipo, apenas_ativos)


@router.get("/resumo", response_model=CertificadoResumo)
async def resumo_certificados(
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> CertificadoResumo:
    return CertificadoResumo(**await svc.resumo(usuario_id))


@router.post("/importar", response_model=CertificadoResponse, status_code=status.HTTP_201_CREATED)
async def importar_certificado(
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
    nome: Annotated[str, Form(min_length=2)],
    file: Annotated[UploadFile, File(description="Certificado (.pfx/.p12/.cer/.pem)")],
    tipo: Annotated[TipoCertificado | None, Form()] = None,
    senha: Annotated[str | None, Form()] = None,
    empresa_id: Annotated[uuid.UUID | None, Form()] = None,
) -> CertificadoResponse:
    conteudo = await file.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo excede 5 MB.")
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Arquivo vazio.")
    try:
        return await svc.importar(
            conteudo=conteudo,
            senha=senha or None,
            nome=nome,
            tipo=tipo,
            empresa_id=empresa_id,
            arquivo_nome=file.filename or "certificado",
            usuario_id=usuario_id,
        )
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.post("", response_model=CertificadoResponse, status_code=status.HTTP_201_CREATED)
async def criar_certificado_manual(
    data: CertificadoManualCreate,
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> CertificadoResponse:
    try:
        return await svc.criar_manual(data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.put("/{certificado_id}", response_model=CertificadoResponse)
async def atualizar_certificado(
    certificado_id: uuid.UUID,
    data: CertificadoUpdate,
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> CertificadoResponse:
    try:
        return await svc.atualizar(certificado_id, data, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.patch("/{certificado_id}/inativar", response_model=CertificadoResponse)
async def inativar_certificado(
    certificado_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> CertificadoResponse:
    try:
        return await svc.inativar(certificado_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc


@router.get("/{certificado_id}/download")
async def baixar_certificado(
    certificado_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> Response:
    try:
        conteudo, nome = await svc.baixar_arquivo(certificado_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    nome_limpo = "".join(c for c in nome if c.isprintable() and c not in '"\r\n')
    return Response(
        content=conteudo,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_limpo}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{certificado_id}/senha")
async def revelar_senha(
    certificado_id: uuid.UUID,
    usuario_id: CurrentUserId,
    svc: Annotated[CertificadoService, Depends(_svc)],
) -> dict[str, str]:
    try:
        senha = await svc.obter_senha(certificado_id, usuario_id)
    except DomainError as exc:
        raise _handle_domain(exc) from exc
    return {"senha": senha}
