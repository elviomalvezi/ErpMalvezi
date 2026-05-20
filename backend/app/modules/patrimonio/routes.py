import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUserId
from app.core.exceptions import DomainError, NotFoundError, PermissionDeniedError
from app.core.storage import StorageProvider, get_storage_provider
from app.core.utils import new_uuid
from app.modules.patrimonio.models import ImovelAnexo, StatusImovel, StatusVeiculo, VeiculoAnexo
from app.modules.patrimonio.repository import ImovelRepository, VeiculoRepository
from app.modules.patrimonio.schemas import (
    ImovelCreate,
    ImovelResponse,
    ImovelUpdate,
    PatrimonioAnexoResponse,
    VeiculoCreate,
    VeiculoResponse,
    VeiculoUpdate,
)
from app.modules.patrimonio.service import ImovelService, VeiculoService

router = APIRouter(prefix="/patrimonio", tags=["patrimônio"])

_MIME_PERMITIDOS = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv", "text/plain",
}
_MAX_BYTES = 10 * 1024 * 1024


def _resp_veiculo(a: VeiculoAnexo) -> PatrimonioAnexoResponse:
    return PatrimonioAnexoResponse(
        id=a.id, registro_id=a.veiculo_id, usuario_id=a.usuario_id,
        nome_original=a.nome_original, tamanho=a.tamanho, mime_type=a.mime_type, criado_em=a.criado_em,
    )


def _resp_imovel(a: ImovelAnexo) -> PatrimonioAnexoResponse:
    return PatrimonioAnexoResponse(
        id=a.id, registro_id=a.imovel_id, usuario_id=a.usuario_id,
        nome_original=a.nome_original, tamanho=a.tamanho, mime_type=a.mime_type, criado_em=a.criado_em,
    )

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _handle(exc: DomainError) -> HTTPException:
    from app.core.exceptions import ConflictError

    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, PermissionDeniedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


# ─────────────────────────────────────── Veículos ────────────────────────────


@router.get("/veiculos", response_model=list[VeiculoResponse])
async def listar_veiculos(
    usuario_id: CurrentUserId,
    db: DbDep,
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    status_v: Annotated[StatusVeiculo | None, Query(alias="status")] = None,
    apenas_ativos: Annotated[bool, Query()] = True,
) -> list[VeiculoResponse]:
    svc = VeiculoService(VeiculoRepository(db))
    veiculos = await svc.listar(usuario_id, empresa_id, status_v, apenas_ativos)
    return [VeiculoResponse.model_validate(v) for v in veiculos]


@router.post("/veiculos", response_model=VeiculoResponse, status_code=status.HTTP_201_CREATED)
async def criar_veiculo(
    data: VeiculoCreate,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> VeiculoResponse:
    svc = VeiculoService(VeiculoRepository(db))
    try:
        v = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return VeiculoResponse.model_validate(v)


@router.get("/veiculos/{veiculo_id}", response_model=VeiculoResponse)
async def obter_veiculo(
    veiculo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> VeiculoResponse:
    svc = VeiculoService(VeiculoRepository(db))
    try:
        v = await svc.obter(veiculo_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return VeiculoResponse.model_validate(v)


@router.put("/veiculos/{veiculo_id}", response_model=VeiculoResponse)
async def atualizar_veiculo(
    veiculo_id: uuid.UUID,
    data: VeiculoUpdate,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> VeiculoResponse:
    svc = VeiculoService(VeiculoRepository(db))
    try:
        v = await svc.atualizar(veiculo_id, data, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return VeiculoResponse.model_validate(v)


@router.patch("/veiculos/{veiculo_id}/inativar", response_model=VeiculoResponse)
async def inativar_veiculo(
    veiculo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> VeiculoResponse:
    svc = VeiculoService(VeiculoRepository(db))
    try:
        v = await svc.inativar(veiculo_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return VeiculoResponse.model_validate(v)


@router.patch("/veiculos/{veiculo_id}/reativar", response_model=VeiculoResponse)
async def reativar_veiculo(
    veiculo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> VeiculoResponse:
    svc = VeiculoService(VeiculoRepository(db))
    try:
        v = await svc.reativar(veiculo_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return VeiculoResponse.model_validate(v)


# ─────────────────────────────────────── Imóveis ─────────────────────────────


@router.get("/imoveis", response_model=list[ImovelResponse])
async def listar_imoveis(
    usuario_id: CurrentUserId,
    db: DbDep,
    empresa_id: Annotated[uuid.UUID | None, Query()] = None,
    status_i: Annotated[StatusImovel | None, Query(alias="status")] = None,
    apenas_ativos: Annotated[bool, Query()] = True,
) -> list[ImovelResponse]:
    svc = ImovelService(ImovelRepository(db))
    imoveis = await svc.listar(usuario_id, empresa_id, status_i, apenas_ativos)
    return [ImovelResponse.model_validate(i) for i in imoveis]


@router.post("/imoveis", response_model=ImovelResponse, status_code=status.HTTP_201_CREATED)
async def criar_imovel(
    data: ImovelCreate,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> ImovelResponse:
    svc = ImovelService(ImovelRepository(db))
    try:
        i = await svc.criar(data, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return ImovelResponse.model_validate(i)


@router.get("/imoveis/{imovel_id}", response_model=ImovelResponse)
async def obter_imovel(
    imovel_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> ImovelResponse:
    svc = ImovelService(ImovelRepository(db))
    try:
        i = await svc.obter(imovel_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return ImovelResponse.model_validate(i)


@router.put("/imoveis/{imovel_id}", response_model=ImovelResponse)
async def atualizar_imovel(
    imovel_id: uuid.UUID,
    data: ImovelUpdate,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> ImovelResponse:
    svc = ImovelService(ImovelRepository(db))
    try:
        i = await svc.atualizar(imovel_id, data, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return ImovelResponse.model_validate(i)


@router.patch("/imoveis/{imovel_id}/inativar", response_model=ImovelResponse)
async def inativar_imovel(
    imovel_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> ImovelResponse:
    svc = ImovelService(ImovelRepository(db))
    try:
        i = await svc.inativar(imovel_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return ImovelResponse.model_validate(i)


@router.patch("/imoveis/{imovel_id}/reativar", response_model=ImovelResponse)
async def reativar_imovel(
    imovel_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
) -> ImovelResponse:
    svc = ImovelService(ImovelRepository(db))
    try:
        i = await svc.reativar(imovel_id, usuario_id)
    except DomainError as exc:
        raise _handle(exc) from exc
    return ImovelResponse.model_validate(i)


# ── Anexos de Veículo ─────────────────────────────────────────────────────────

async def _get_veiculo_ou_404(veiculo_id: uuid.UUID, usuario_id: uuid.UUID, db: AsyncSession) -> None:
    from app.modules.patrimonio.models import Veiculo as VeiculoModel
    result = await db.execute(
        select(VeiculoModel).where(
            VeiculoModel.id == veiculo_id,
            VeiculoModel.usuario_id == usuario_id,
            VeiculoModel.ativo.is_(True),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")


@router.get("/veiculos/{veiculo_id}/anexos", response_model=list[PatrimonioAnexoResponse])
async def listar_anexos_veiculo(
    veiculo_id: uuid.UUID, usuario_id: CurrentUserId, db: DbDep,
) -> list[PatrimonioAnexoResponse]:
    await _get_veiculo_ou_404(veiculo_id, usuario_id, db)
    result = await db.execute(
        select(VeiculoAnexo).where(
            VeiculoAnexo.veiculo_id == veiculo_id, VeiculoAnexo.ativo.is_(True),
        ).order_by(VeiculoAnexo.criado_em)
    )
    return [_resp_veiculo(a) for a in result.scalars().all()]


@router.post("/veiculos/{veiculo_id}/anexos", response_model=PatrimonioAnexoResponse, status_code=201)
async def upload_anexo_veiculo(
    veiculo_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
    file: Annotated[UploadFile, File()],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> PatrimonioAnexoResponse:
    await _get_veiculo_ou_404(veiculo_id, usuario_id, db)
    conteudo = await file.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede 10 MB.")
    mime = file.content_type or "application/octet-stream"
    if mime not in _MIME_PERMITIDOS:
        raise HTTPException(status_code=415, detail=f"Tipo não permitido: {mime}")
    nome = file.filename or "arquivo"
    ext = nome.rsplit(".", 1)[-1] if "." in nome else "bin"
    caminho = f"anexos/veiculo/{veiculo_id}/{new_uuid()}.{ext}"
    await storage.salvar(conteudo, caminho, mime)
    anexo = VeiculoAnexo(id=new_uuid(), veiculo_id=veiculo_id, usuario_id=usuario_id,
                         nome_original=nome, tamanho=len(conteudo), mime_type=mime, caminho=caminho)
    db.add(anexo)
    await db.commit()
    await db.refresh(anexo)
    return _resp_veiculo(anexo)


@router.delete("/veiculos/{veiculo_id}/anexos/{anexo_id}", status_code=204)
async def deletar_anexo_veiculo(
    veiculo_id: uuid.UUID, anexo_id: uuid.UUID,
    usuario_id: CurrentUserId, db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> None:
    await _get_veiculo_ou_404(veiculo_id, usuario_id, db)
    result = await db.execute(
        select(VeiculoAnexo).where(VeiculoAnexo.id == anexo_id, VeiculoAnexo.veiculo_id == veiculo_id, VeiculoAnexo.ativo.is_(True))
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    await storage.excluir(anexo.caminho)
    anexo.ativo = False
    await db.commit()


@router.get("/veiculos/{veiculo_id}/anexos/{anexo_id}/download")
async def download_anexo_veiculo(
    veiculo_id: uuid.UUID, anexo_id: uuid.UUID,
    usuario_id: CurrentUserId, db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> Response:
    await _get_veiculo_ou_404(veiculo_id, usuario_id, db)
    result = await db.execute(
        select(VeiculoAnexo).where(VeiculoAnexo.id == anexo_id, VeiculoAnexo.veiculo_id == veiculo_id, VeiculoAnexo.ativo.is_(True))
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    try:
        conteudo = await storage.ler(anexo.caminho)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage.")
    return Response(content=conteudo, media_type=anexo.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{anexo.nome_original}"'})


# ── Anexos de Imóvel ──────────────────────────────────────────────────────────

async def _get_imovel_ou_404(imovel_id: uuid.UUID, usuario_id: uuid.UUID, db: AsyncSession) -> None:
    from app.modules.patrimonio.models import Imovel as ImovelModel
    result = await db.execute(
        select(ImovelModel).where(
            ImovelModel.id == imovel_id,
            ImovelModel.usuario_id == usuario_id,
            ImovelModel.ativo.is_(True),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imóvel não encontrado.")


@router.get("/imoveis/{imovel_id}/anexos", response_model=list[PatrimonioAnexoResponse])
async def listar_anexos_imovel(
    imovel_id: uuid.UUID, usuario_id: CurrentUserId, db: DbDep,
) -> list[PatrimonioAnexoResponse]:
    await _get_imovel_ou_404(imovel_id, usuario_id, db)
    result = await db.execute(
        select(ImovelAnexo).where(
            ImovelAnexo.imovel_id == imovel_id, ImovelAnexo.ativo.is_(True),
        ).order_by(ImovelAnexo.criado_em)
    )
    return [_resp_imovel(a) for a in result.scalars().all()]


@router.post("/imoveis/{imovel_id}/anexos", response_model=PatrimonioAnexoResponse, status_code=201)
async def upload_anexo_imovel(
    imovel_id: uuid.UUID,
    usuario_id: CurrentUserId,
    db: DbDep,
    file: Annotated[UploadFile, File()],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> PatrimonioAnexoResponse:
    await _get_imovel_ou_404(imovel_id, usuario_id, db)
    conteudo = await file.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede 10 MB.")
    mime = file.content_type or "application/octet-stream"
    if mime not in _MIME_PERMITIDOS:
        raise HTTPException(status_code=415, detail=f"Tipo não permitido: {mime}")
    nome = file.filename or "arquivo"
    ext = nome.rsplit(".", 1)[-1] if "." in nome else "bin"
    caminho = f"anexos/imovel/{imovel_id}/{new_uuid()}.{ext}"
    await storage.salvar(conteudo, caminho, mime)
    anexo = ImovelAnexo(id=new_uuid(), imovel_id=imovel_id, usuario_id=usuario_id,
                        nome_original=nome, tamanho=len(conteudo), mime_type=mime, caminho=caminho)
    db.add(anexo)
    await db.commit()
    await db.refresh(anexo)
    return _resp_imovel(anexo)


@router.delete("/imoveis/{imovel_id}/anexos/{anexo_id}", status_code=204)
async def deletar_anexo_imovel(
    imovel_id: uuid.UUID, anexo_id: uuid.UUID,
    usuario_id: CurrentUserId, db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> None:
    await _get_imovel_ou_404(imovel_id, usuario_id, db)
    result = await db.execute(
        select(ImovelAnexo).where(ImovelAnexo.id == anexo_id, ImovelAnexo.imovel_id == imovel_id, ImovelAnexo.ativo.is_(True))
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    await storage.excluir(anexo.caminho)
    anexo.ativo = False
    await db.commit()


@router.get("/imoveis/{imovel_id}/anexos/{anexo_id}/download")
async def download_anexo_imovel(
    imovel_id: uuid.UUID, anexo_id: uuid.UUID,
    usuario_id: CurrentUserId, db: DbDep,
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> Response:
    await _get_imovel_ou_404(imovel_id, usuario_id, db)
    result = await db.execute(
        select(ImovelAnexo).where(ImovelAnexo.id == anexo_id, ImovelAnexo.imovel_id == imovel_id, ImovelAnexo.ativo.is_(True))
    )
    anexo = result.scalar_one_or_none()
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    try:
        conteudo = await storage.ler(anexo.caminho)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage.")
    return Response(content=conteudo, media_type=anexo.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{anexo.nome_original}"'})
