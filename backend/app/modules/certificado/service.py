import uuid
from datetime import date

import structlog

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.certificado.crypto_util import cifrar, decifrar
from app.modules.certificado.models import Certificado, TipoCertificado
from app.modules.certificado.parser import parse_certificado
from app.modules.certificado.repository import CertificadoRepository
from app.modules.certificado.schemas import (
    CertificadoManualCreate,
    CertificadoResponse,
    CertificadoUpdate,
)

logger = structlog.get_logger()

_DIAS_ALERTA = 30


def _status(validade_fim: date | None, hoje: date) -> tuple[str, int | None]:
    if validade_fim is None:
        return "sem_data", None
    dias = (validade_fim - hoje).days
    if dias < 0:
        return "vencido", dias
    if dias <= _DIAS_ALERTA:
        return "vencendo", dias
    return "valido", dias


class CertificadoService:
    def __init__(self, repo: CertificadoRepository) -> None:
        self._repo = repo

    def _to_response(
        self, cert: Certificado, hoje: date, nome_empresa: str | None
    ) -> CertificadoResponse:
        status_validade, dias = _status(cert.validade_fim, hoje)
        return CertificadoResponse(
            id=cert.id,
            empresa_id=cert.empresa_id,
            nome_empresa=nome_empresa,
            nome=cert.nome,
            tipo=cert.tipo,
            titular=cert.titular,
            documento=cert.documento,
            emissor=cert.emissor,
            numero_serie=cert.numero_serie,
            validade_inicio=cert.validade_inicio,
            validade_fim=cert.validade_fim,
            formato=cert.formato,
            arquivo_nome=cert.arquivo_nome,
            tem_arquivo=cert.arquivo_nome is not None,
            tem_senha=cert.senha_cifrada is not None,
            observacoes=cert.observacoes,
            ativo=cert.ativo,
            dias_para_vencer=dias,
            status_validade=status_validade,
        )

    async def _nome_empresa(self, empresa_id: uuid.UUID | None) -> str | None:
        if empresa_id is None:
            return None
        return (await self._repo.empresas_nomes([empresa_id])).get(empresa_id)

    async def listar(
        self,
        usuario_id: uuid.UUID,
        tipo: TipoCertificado | None = None,
        apenas_ativos: bool = True,
    ) -> list[CertificadoResponse]:
        hoje = date.today()
        certs = await self._repo.listar(usuario_id, tipo, apenas_ativos)
        ids = list({c.empresa_id for c in certs if c.empresa_id})
        nomes = await self._repo.empresas_nomes(ids)
        return [self._to_response(c, hoje, nomes.get(c.empresa_id)) for c in certs]

    async def resumo(self, usuario_id: uuid.UUID) -> dict[str, int]:
        hoje = date.today()
        certs = await self._repo.listar(usuario_id, None, apenas_ativos=True)
        contagem = {"total": len(certs), "validos": 0, "vencendo": 0, "vencido": 0}
        for c in certs:
            status, _ = _status(c.validade_fim, hoje)
            if status == "valido":
                contagem["validos"] += 1
            elif status == "vencendo":
                contagem["vencendo"] += 1
            elif status == "vencido":
                contagem["vencido"] += 1
        return contagem

    async def importar(
        self,
        conteudo: bytes,
        senha: str | None,
        nome: str,
        tipo: TipoCertificado | None,
        empresa_id: uuid.UUID | None,
        arquivo_nome: str,
        usuario_id: uuid.UUID,
    ) -> CertificadoResponse:
        if empresa_id is not None and not await self._repo.acesso_empresa(usuario_id, empresa_id):
            raise PermissionDeniedError("Sem acesso à empresa selecionada.")

        meta = parse_certificado(conteudo, senha, arquivo_nome)
        # Tipo: usa o informado ou o detectado automaticamente no certificado.
        tipo_final = tipo or TipoCertificado(meta["tipo_sugerido"])
        # Auto-vínculo: se nenhuma empresa foi escolhida, tenta casar pelo CNPJ/CPF.
        if empresa_id is None and meta["documento"]:
            empresa_id = await self._repo.empresa_por_documento(meta["documento"], usuario_id)

        cert = Certificado(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            nome=nome,
            tipo=tipo_final,
            titular=meta["titular"],
            documento=meta["documento"],
            emissor=meta["emissor"],
            numero_serie=meta["numero_serie"],
            validade_inicio=meta["validade_inicio"],
            validade_fim=meta["validade_fim"],
            formato=meta["formato"],
            arquivo_nome=arquivo_nome[:255],
            arquivo=conteudo,
            senha_cifrada=cifrar(senha) if senha else None,
        )
        await self._repo.create(cert)
        await self._repo.commit()
        await self._repo.refresh(cert)
        logger.info("certificado_importado", certificado_id=str(cert.id), tipo=tipo)
        return self._to_response(cert, date.today(), await self._nome_empresa(empresa_id))

    async def criar_manual(
        self, data: CertificadoManualCreate, usuario_id: uuid.UUID
    ) -> CertificadoResponse:
        if data.empresa_id is not None and not await self._repo.acesso_empresa(
            usuario_id, data.empresa_id
        ):
            raise PermissionDeniedError("Sem acesso à empresa selecionada.")
        cert = Certificado(
            empresa_id=data.empresa_id,
            usuario_id=usuario_id,
            nome=data.nome,
            tipo=data.tipo,
            titular=data.titular,
            documento=data.documento,
            emissor=data.emissor,
            numero_serie=data.numero_serie,
            validade_inicio=data.validade_inicio,
            validade_fim=data.validade_fim,
            observacoes=data.observacoes,
        )
        await self._repo.create(cert)
        await self._repo.commit()
        await self._repo.refresh(cert)
        return self._to_response(cert, date.today(), await self._nome_empresa(data.empresa_id))

    async def obter(self, certificado_id: uuid.UUID, usuario_id: uuid.UUID) -> Certificado:
        cert = await self._repo.get_by_id(certificado_id)
        if cert is None:
            raise NotFoundError("Certificado não encontrado.")
        if not await self._repo.tem_acesso(certificado_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a este certificado.")
        return cert

    async def atualizar(
        self, certificado_id: uuid.UUID, data: CertificadoUpdate, usuario_id: uuid.UUID
    ) -> CertificadoResponse:
        cert = await self.obter(certificado_id, usuario_id)
        update_data = data.model_dump(exclude_unset=True)
        # Datas de validade são imutáveis após a inclusão.
        update_data.pop("validade_inicio", None)
        update_data.pop("validade_fim", None)
        if update_data.get("empresa_id") is not None and not await self._repo.acesso_empresa(
            usuario_id, update_data["empresa_id"]
        ):
            raise PermissionDeniedError("Sem acesso à empresa selecionada.")
        for field, value in update_data.items():
            setattr(cert, field, value)
        await self._repo.commit()
        await self._repo.refresh(cert)
        return self._to_response(cert, date.today(), await self._nome_empresa(cert.empresa_id))

    async def inativar(
        self, certificado_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> CertificadoResponse:
        cert = await self.obter(certificado_id, usuario_id)
        if not cert.ativo:
            raise ConflictError("Certificado já está inativo.")
        cert.ativo = False
        await self._repo.commit()
        await self._repo.refresh(cert)
        return self._to_response(cert, date.today(), await self._nome_empresa(cert.empresa_id))

    async def baixar_arquivo(
        self, certificado_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> tuple[bytes, str]:
        # Valida acesso/existência e carrega o blob com SELECT explícito
        # (a coluna arquivo é deferred; lazy-load não funciona em async).
        await self.obter(certificado_id, usuario_id)
        conteudo, nome = await self._repo.get_arquivo(certificado_id)
        if conteudo is None:
            raise NotFoundError("Este certificado não possui arquivo armazenado.")
        return conteudo, (nome or "certificado")

    async def obter_senha(self, certificado_id: uuid.UUID, usuario_id: uuid.UUID) -> str:
        cert = await self.obter(certificado_id, usuario_id)
        if not cert.senha_cifrada:
            raise NotFoundError("Este certificado não possui senha armazenada.")
        return decifrar(cert.senha_cifrada)
