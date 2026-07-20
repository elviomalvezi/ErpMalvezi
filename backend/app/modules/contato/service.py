import uuid

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.contato.models import Contato, EscopoContato, TipoContato
from app.modules.contato.repository import ContatoRepository
from app.modules.contato.schemas import ContatoCreate, ContatoUpdate
from app.modules.empresa.validators import validar_cnpj, validar_cpf

logger = structlog.get_logger()


class ContatoService:
    def __init__(self, repo: ContatoRepository) -> None:
        self._repo = repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        eh_cliente: bool | None = None,
        eh_fornecedor: bool | None = None,
        apenas_ativas: bool = True,
    ) -> list[Contato]:
        return await self._repo.listar(
            usuario_id, empresa_id, eh_cliente, eh_fornecedor, apenas_ativas
        )

    async def obter(self, contato_id: uuid.UUID, usuario_id: uuid.UUID) -> Contato:
        contato = await self._repo.get_by_id(contato_id)
        if contato is None:
            raise NotFoundError("Contato não encontrado.")
        if not await self._repo.tem_acesso(contato_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a este contato.")
        return contato

    async def criar(self, data: ContatoCreate, usuario_id: uuid.UUID) -> Contato:
        if await self._repo.ja_existe_documento(usuario_id, data.documento):
            raise ConflictError("Já existe um contato com este documento.")

        contato = Contato(
            usuario_id=usuario_id,
            empresa_id=data.empresa_id,
            tipo=data.tipo,
            documento=data.documento,
            nome_principal=data.nome_principal,
            nome_alternativo=data.nome_alternativo,
            eh_cliente=data.eh_cliente,
            eh_fornecedor=data.eh_fornecedor,
            escopo=data.escopo,
            email=data.email,
            telefone=data.telefone,
            celular=data.celular,
            site=data.site,
            cep=data.cep,
            logradouro=data.logradouro,
            numero=data.numero,
            complemento=data.complemento,
            bairro=data.bairro,
            cidade=data.cidade,
            uf=data.uf,
            pais=data.pais,
            observacoes=data.observacoes,
        )
        await self._repo.create(contato)
        await self._repo.commit()
        await self._repo.refresh(contato)
        logger.info(
            "contato_criado",
            nome=data.nome_principal,
            tipo=data.tipo,
            usuario_id=str(usuario_id),
        )
        return contato

    async def atualizar(
        self, contato_id: uuid.UUID, data: ContatoUpdate, usuario_id: uuid.UUID
    ) -> Contato:
        contato = await self.obter(contato_id, usuario_id)
        update_data = data.model_dump(exclude_unset=True)

        if "documento" in update_data:
            novo_doc = update_data["documento"]
            _validar_doc_por_tipo(novo_doc, contato.tipo)
            if await self._repo.ja_existe_documento(usuario_id, novo_doc, excluir_id=contato_id):
                raise ConflictError("Já existe outro contato com este documento.")

        eh_cliente = update_data.get("eh_cliente", contato.eh_cliente)
        eh_fornecedor = update_data.get("eh_fornecedor", contato.eh_fornecedor)
        if not eh_cliente and not eh_fornecedor:
            raise DomainError("O contato deve ser cliente, fornecedor ou ambos.")

        novo_escopo = update_data.get("escopo", contato.escopo)
        nova_empresa = update_data.get("empresa_id", contato.empresa_id)
        if novo_escopo == EscopoContato.ESPECIFICO and nova_empresa is None:
            raise DomainError("empresa_id é obrigatório quando escopo é 'especifico'.")
        if novo_escopo == EscopoContato.GLOBAL and nova_empresa is not None:
            raise DomainError("empresa_id deve ser nulo quando escopo é 'global'.")

        for field, value in update_data.items():
            setattr(contato, field, value)
        await self._repo.commit()
        await self._repo.refresh(contato)
        return contato

    async def inativar(self, contato_id: uuid.UUID, usuario_id: uuid.UUID) -> Contato:
        contato = await self.obter(contato_id, usuario_id)
        if not contato.ativa:
            raise ConflictError("Contato já está inativo.")
        if await self._repo.has_lancamentos(contato_id):
            raise DomainError("Não é possível inativar um contato com lançamentos vinculados.")
        contato.ativa = False
        await self._repo.commit()
        await self._repo.refresh(contato)
        logger.info("contato_inativado", contato_id=str(contato_id))
        return contato

    async def reativar(self, contato_id: uuid.UUID, usuario_id: uuid.UUID) -> Contato:
        contato = await self.obter(contato_id, usuario_id)
        if contato.ativa:
            raise ConflictError("Contato já está ativo.")
        contato.ativa = True
        await self._repo.commit()
        await self._repo.refresh(contato)
        return contato

    async def merge(
        self,
        origem_id: uuid.UUID,
        destino_id: uuid.UUID,
        usuario_id: uuid.UUID,
    ) -> Contato:
        from app.modules.lancamento.models import Lancamento
        from sqlalchemy import update

        origem = await self.obter(origem_id, usuario_id)
        destino = await self.obter(destino_id, usuario_id)

        if origem_id == destino_id:
            raise DomainError("Origem e destino devem ser diferentes.")

        # Reassociar lançamentos
        await self._repo._db.execute(
            update(Lancamento)
            .where(Lancamento.contato_id == origem_id)
            .values(contato_id=destino_id)
        )

        # Inativar o contato de origem
        origem.ativa = False
        await self._repo.commit()
        await self._repo.refresh(destino)
        return destino


def _validar_doc_por_tipo(documento: str, tipo: TipoContato) -> None:
    if tipo == TipoContato.PJ and not validar_cnpj(documento):
        raise DomainError("CNPJ inválido.")
    if tipo == TipoContato.PF and not validar_cpf(documento):
        raise DomainError("CPF inválido.")
