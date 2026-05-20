import uuid
from datetime import date

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.transferencia.models import StatusTransferencia, Transferencia
from app.modules.transferencia.repository import TransferenciaRepository
from app.modules.transferencia.schemas import TransferenciaCreate

logger = structlog.get_logger()


class TransferenciaService:
    def __init__(
        self,
        repo: TransferenciaRepository,
        conta_repo: ContaBancariaRepository,
    ) -> None:
        self._repo = repo
        self._conta_repo = conta_repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        conta_id: uuid.UUID | None = None,
        status: StatusTransferencia | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        apenas_ativas: bool = True,
    ) -> list[Transferencia]:
        return await self._repo.listar(
            usuario_id, empresa_id, conta_id, status, data_inicio, data_fim, apenas_ativas
        )

    async def obter(
        self, transferencia_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> Transferencia:
        transf = await self._repo.get_by_id(transferencia_id)
        if transf is None:
            raise NotFoundError("Transferência não encontrada.")
        if transf.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a esta transferência.")
        return transf

    async def criar(
        self, data: TransferenciaCreate, usuario_id: uuid.UUID
    ) -> Transferencia:
        conta_origem = await self._conta_repo.get_by_id(data.conta_origem_id)
        if conta_origem is None:
            raise NotFoundError("Conta de origem não encontrada.")
        if conta_origem.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso à conta de origem.")
        if conta_origem.tipo == TipoConta.CARTAO_CREDITO:
            raise DomainError(
                "Não é possível transferir a partir de um cartão de crédito. "
                "Use o pagamento de fatura."
            )

        conta_destino = await self._conta_repo.get_by_id(data.conta_destino_id)
        if conta_destino is None:
            raise NotFoundError("Conta de destino não encontrada.")
        if conta_destino.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso à conta de destino.")
        if conta_destino.tipo == TipoConta.CARTAO_CREDITO:
            raise DomainError(
                "Não é possível transferir para um cartão de crédito. "
                "Use o pagamento de fatura."
            )

        transf = Transferencia(
            usuario_id=usuario_id,
            empresa_origem_id=data.empresa_origem_id,
            empresa_destino_id=data.empresa_destino_id,
            conta_origem_id=data.conta_origem_id,
            conta_destino_id=data.conta_destino_id,
            valor=data.valor,
            data_transferencia=data.data_transferencia,
            descricao=data.descricao,
            status=StatusTransferencia.CONCLUIDA,
        )
        await self._repo.create(transf)
        logger.info(
            "transferencia_criada",
            valor=str(data.valor),
            conta_origem_id=str(data.conta_origem_id),
            conta_destino_id=str(data.conta_destino_id),
            usuario_id=str(usuario_id),
        )
        return transf

    async def cancelar(
        self, transferencia_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> Transferencia:
        transf = await self.obter(transferencia_id, usuario_id)
        if transf.status == StatusTransferencia.CANCELADA:
            raise ConflictError("Transferência já está cancelada.")
        transf.status = StatusTransferencia.CANCELADA
        transf.ativo = False
        logger.info("transferencia_cancelada", transferencia_id=str(transferencia_id))
        return transf
