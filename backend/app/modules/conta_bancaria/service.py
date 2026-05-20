import uuid

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.conta_bancaria.schemas import ContaBancariaCreate, ContaBancariaUpdate

logger = structlog.get_logger()


class ContaBancariaService:
    def __init__(self, repo: ContaBancariaRepository) -> None:
        self._repo = repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        tipo: TipoConta | None = None,
        apenas_ativas: bool = True,
    ) -> list[ContaBancaria]:
        return await self._repo.listar(usuario_id, empresa_id, tipo, apenas_ativas)

    async def obter(self, conta_id: uuid.UUID, usuario_id: uuid.UUID) -> ContaBancaria:
        conta = await self._repo.get_by_id(conta_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")
        if conta.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a esta conta bancária.")
        return conta

    async def criar(self, data: ContaBancariaCreate, usuario_id: uuid.UUID) -> ContaBancaria:
        conta = ContaBancaria(
            empresa_id=data.empresa_id,
            usuario_id=usuario_id,
            nome=data.nome,
            tipo=data.tipo,
            banco=data.banco,
            agencia=data.agencia,
            numero_conta=data.numero_conta,
            digito=data.digito,
            saldo_inicial=data.saldo_inicial,
            data_saldo_inicial=data.data_saldo_inicial,
            bandeira=data.bandeira,
            limite=data.limite,
            dia_vencimento=data.dia_vencimento,
            dia_fechamento=data.dia_fechamento,
        )
        await self._repo.create(conta)
        await self._repo.commit()
        await self._repo.refresh(conta)
        logger.info(
            "conta_bancaria_criada",
            nome=data.nome,
            tipo=data.tipo,
            empresa_id=str(data.empresa_id),
            usuario_id=str(usuario_id),
        )
        return conta

    async def atualizar(
        self, conta_id: uuid.UUID, data: ContaBancariaUpdate, usuario_id: uuid.UUID
    ) -> ContaBancaria:
        conta = await self.obter(conta_id, usuario_id)
        update_data = data.model_dump(exclude_unset=True)

        if conta.tipo == TipoConta.CARTAO_CREDITO:
            # Para cartão, valida que não está zerando campos obrigatórios
            novo_limite = update_data.get("limite", conta.limite)
            novo_venc = update_data.get("dia_vencimento", conta.dia_vencimento)
            novo_fech = update_data.get("dia_fechamento", conta.dia_fechamento)
            if novo_limite is None:
                raise DomainError("limite não pode ser removido de um cartão de crédito.")
            if novo_venc is None:
                raise DomainError("dia_vencimento não pode ser removido de um cartão de crédito.")
            if novo_fech is None:
                raise DomainError("dia_fechamento não pode ser removido de um cartão de crédito.")
        else:
            # Para contas não-cartão, bloqueia campos de cartão
            campos_cartao = {"bandeira", "limite", "dia_vencimento", "dia_fechamento"}
            for campo in campos_cartao & update_data.keys():
                if update_data[campo] is not None:
                    raise DomainError(
                        f"Campo '{campo}' é exclusivo de cartão de crédito."
                    )

        for field, value in update_data.items():
            setattr(conta, field, value)
        await self._repo.commit()
        await self._repo.refresh(conta)
        return conta

    async def inativar(self, conta_id: uuid.UUID, usuario_id: uuid.UUID) -> ContaBancaria:
        conta = await self.obter(conta_id, usuario_id)
        if not conta.ativa:
            raise ConflictError("Conta bancária já está inativa.")
        if await self._repo.has_lancamentos(conta_id):
            raise DomainError(
                "Não é possível inativar uma conta com lançamentos vinculados."
            )
        conta.ativa = False
        await self._repo.commit()
        await self._repo.refresh(conta)
        logger.info("conta_bancaria_inativada", conta_id=str(conta_id))
        return conta

    async def reativar(self, conta_id: uuid.UUID, usuario_id: uuid.UUID) -> ContaBancaria:
        conta = await self.obter(conta_id, usuario_id)
        if conta.ativa:
            raise ConflictError("Conta bancária já está ativa.")
        conta.ativa = True
        await self._repo.commit()
        await self._repo.refresh(conta)
        return conta
