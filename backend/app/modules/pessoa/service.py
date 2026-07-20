import uuid
from datetime import date

import structlog

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.certificado.service import _status
from app.modules.pessoa.models import Pessoa
from app.modules.pessoa.repository import PessoaRepository
from app.modules.pessoa.schemas import (
    CertificadoResumoItem,
    PessoaCreate,
    PessoaDetalhe,
    PessoaResponse,
    PessoaUpdate,
)

logger = structlog.get_logger()


class PessoaService:
    def __init__(self, repo: PessoaRepository) -> None:
        self._repo = repo

    def _to_response(self, pessoa: Pessoa, total: int = 0) -> PessoaResponse:
        return PessoaResponse(
            id=pessoa.id,
            nome=pessoa.nome,
            email=pessoa.email,
            tipo=pessoa.tipo,
            setor=pessoa.setor,
            empresa_externa=pessoa.empresa_externa,
            telefone=pessoa.telefone,
            observacoes=pessoa.observacoes,
            ativo=pessoa.ativo,
            total_certificados=total,
        )

    async def _validar_certs(self, cert_ids: list[uuid.UUID]) -> None:
        for cid in cert_ids:
            if not await self._repo.cert_existe(cid):
                raise NotFoundError("Um dos certificados selecionados não existe.")

    async def listar(self, usuario_id: uuid.UUID, apenas_ativos: bool = True) -> list[PessoaResponse]:
        pessoas = await self._repo.listar(apenas_ativos)
        totais = await self._repo.total_por_pessoa([p.id for p in pessoas])
        return [self._to_response(p, totais.get(p.id, 0)) for p in pessoas]

    async def obter(self, pessoa_id: uuid.UUID, usuario_id: uuid.UUID) -> PessoaDetalhe:
        pessoa = await self._repo.get_by_id(pessoa_id)
        if pessoa is None:
            raise NotFoundError("Pessoa não encontrada.")
        certs = await self._repo.certificados_de_pessoa(pessoa_id)
        hoje = date.today()
        nomes = await self._repo.empresas_nomes(list({c.empresa_id for c in certs if c.empresa_id}))
        itens = [
            CertificadoResumoItem(
                id=c.id,
                nome=c.nome,
                tipo=c.tipo,
                validade_fim=c.validade_fim,
                status_validade=_status(c.validade_fim, hoje)[0],
                empresa_id=c.empresa_id,
                nome_empresa=nomes.get(c.empresa_id),
            )
            for c in certs
        ]
        base = self._to_response(pessoa, len(itens))
        return PessoaDetalhe(**base.model_dump(), certificados=itens)

    async def criar(self, data: PessoaCreate, usuario_id: uuid.UUID) -> PessoaResponse:
        await self._validar_certs(data.certificado_ids)
        pessoa = Pessoa(
            usuario_id=usuario_id,
            nome=data.nome,
            email=data.email,
            tipo=data.tipo,
            setor=data.setor,
            empresa_externa=data.empresa_externa,
            telefone=data.telefone,
            observacoes=data.observacoes,
        )
        await self._repo.create(pessoa)
        for cid in set(data.certificado_ids):
            await self._repo.associar(pessoa.id, cid)
        await self._repo.commit()
        await self._repo.refresh(pessoa)
        logger.info("pessoa_criada", pessoa_id=str(pessoa.id), certs=len(set(data.certificado_ids)))
        return self._to_response(pessoa, len(set(data.certificado_ids)))

    async def atualizar(
        self, pessoa_id: uuid.UUID, data: PessoaUpdate, usuario_id: uuid.UUID
    ) -> PessoaResponse:
        pessoa = await self._repo.get_by_id(pessoa_id)
        if pessoa is None:
            raise NotFoundError("Pessoa não encontrada.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pessoa, field, value)
        await self._repo.commit()
        await self._repo.refresh(pessoa)
        total = (await self._repo.total_por_pessoa([pessoa_id])).get(pessoa_id, 0)
        return self._to_response(pessoa, total)

    async def inativar(self, pessoa_id: uuid.UUID, usuario_id: uuid.UUID) -> PessoaResponse:
        pessoa = await self._repo.get_by_id(pessoa_id)
        if pessoa is None:
            raise NotFoundError("Pessoa não encontrada.")
        if not pessoa.ativo:
            raise ConflictError("Pessoa já está inativa.")
        pessoa.ativo = False
        await self._repo.commit()
        await self._repo.refresh(pessoa)
        return self._to_response(pessoa)

    async def definir_certificados(
        self, pessoa_id: uuid.UUID, cert_ids: list[uuid.UUID], usuario_id: uuid.UUID
    ) -> PessoaDetalhe:
        pessoa = await self._repo.get_by_id(pessoa_id)
        if pessoa is None:
            raise NotFoundError("Pessoa não encontrada.")
        await self._validar_certs(cert_ids)
        atuais = await self._repo.cert_ids_de_pessoa(pessoa_id)
        alvo = set(cert_ids)
        await self._repo.remover_associacoes(pessoa_id, list(atuais - alvo))
        for cid in alvo - atuais:
            await self._repo.associar(pessoa_id, cid)
        await self._repo.commit()
        return await self.obter(pessoa_id, usuario_id)

    # ── Lado do certificado ───────────────────────────────────────────────────
    async def pessoas_do_certificado(
        self, certificado_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> list[PessoaResponse]:
        if not await self._repo.cert_existe(certificado_id):
            raise NotFoundError("Certificado não encontrado.")
        pessoas = await self._repo.pessoas_de_certificado(certificado_id)
        totais = await self._repo.total_por_pessoa([p.id for p in pessoas])
        return [self._to_response(p, totais.get(p.id, 0)) for p in pessoas]

    async def associar_pessoa(
        self, certificado_id: uuid.UUID, pessoa_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> None:
        if not await self._repo.cert_existe(certificado_id):
            raise NotFoundError("Certificado não encontrado.")
        pessoa = await self._repo.get_by_id(pessoa_id)
        if pessoa is None:
            raise NotFoundError("Pessoa não encontrada.")
        if not await self._repo.assoc_existe(pessoa_id, certificado_id):
            await self._repo.associar(pessoa_id, certificado_id)
            await self._repo.commit()

    async def desassociar_pessoa(
        self, certificado_id: uuid.UUID, pessoa_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> None:
        await self._repo.desassociar(pessoa_id, certificado_id)
        await self._repo.commit()
