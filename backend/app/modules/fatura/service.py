import calendar
import uuid
from datetime import date
from decimal import Decimal

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.fatura.models import Fatura, StatusFatura
from app.modules.fatura.repository import FaturaRepository
from app.modules.fatura.schemas import FaturaCreate, FaturaPagamentoCreate

logger = structlog.get_logger()


def _dia_do_mes(ano: int, mes: int, dia: int) -> date:
    ultimo = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo))


def _calcular_datas_fatura(
    competencia: date, dia_fechamento: int, dia_vencimento: int
) -> tuple[date, date]:
    data_fechamento = _dia_do_mes(competencia.year, competencia.month, dia_fechamento)
    if dia_vencimento >= dia_fechamento:
        data_vencimento = _dia_do_mes(
            competencia.year, competencia.month, dia_vencimento
        )
    else:
        # Vencimento cai no mês seguinte
        if competencia.month == 12:
            data_vencimento = _dia_do_mes(competencia.year + 1, 1, dia_vencimento)
        else:
            data_vencimento = _dia_do_mes(
                competencia.year, competencia.month + 1, dia_vencimento
            )
    return data_fechamento, data_vencimento


class FaturaService:
    def __init__(
        self, repo: FaturaRepository, conta_repo: ContaBancariaRepository
    ) -> None:
        self._repo = repo
        self._conta_repo = conta_repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        conta_bancaria_id: uuid.UUID | None = None,
        empresa_id: uuid.UUID | None = None,
        status: StatusFatura | None = None,
        competencia_inicio: date | None = None,
        competencia_fim: date | None = None,
    ) -> list[Fatura]:
        return await self._repo.listar(
            usuario_id, conta_bancaria_id, empresa_id, status,
            competencia_inicio, competencia_fim,
        )

    async def obter(self, fatura_id: uuid.UUID, usuario_id: uuid.UUID) -> Fatura:
        fatura = await self._repo.get_by_id(fatura_id)
        if fatura is None:
            raise NotFoundError("Fatura não encontrada.")
        if fatura.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a esta fatura.")
        return fatura

    async def criar(self, data: FaturaCreate, usuario_id: uuid.UUID) -> Fatura:
        competencia = data.competencia  # já normalizado para dia 1 pelo schema
        return await self._obter_ou_criar(data.conta_bancaria_id, competencia, usuario_id)

    async def obter_ou_criar_fatura_aberta(
        self,
        conta_bancaria_id: uuid.UUID,
        competencia: date,
        usuario_id: uuid.UUID,
    ) -> Fatura:
        competencia_norm = competencia.replace(day=1)
        return await self._obter_ou_criar(conta_bancaria_id, competencia_norm, usuario_id)

    async def _obter_ou_criar(
        self,
        conta_bancaria_id: uuid.UUID,
        competencia: date,
        usuario_id: uuid.UUID,
    ) -> Fatura:
        existente = await self._repo.get_by_conta_competencia(conta_bancaria_id, competencia)
        if existente is not None:
            if existente.usuario_id != usuario_id:
                raise PermissionDeniedError("Sem acesso a esta fatura.")
            return existente

        conta = await self._conta_repo.get_by_id(conta_bancaria_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")
        if conta.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a esta conta bancária.")
        if conta.tipo != TipoConta.CARTAO_CREDITO:
            raise DomainError("A conta informada não é um cartão de crédito.")
        if conta.dia_fechamento is None or conta.dia_vencimento is None:
            raise DomainError(
                "Cartão sem dia de fechamento ou vencimento configurado."
            )

        data_fechamento, data_vencimento = _calcular_datas_fatura(
            competencia, conta.dia_fechamento, conta.dia_vencimento
        )

        fatura = Fatura(
            conta_bancaria_id=conta_bancaria_id,
            empresa_id=conta.empresa_id,
            usuario_id=usuario_id,
            competencia=competencia,
            data_fechamento=data_fechamento,
            data_vencimento=data_vencimento,
        )
        await self._repo.create(fatura)
        logger.info(
            "fatura_criada",
            conta_bancaria_id=str(conta_bancaria_id),
            competencia=str(competencia),
        )
        return fatura

    async def fechar_fatura(self, fatura_id: uuid.UUID, usuario_id: uuid.UUID) -> Fatura:
        fatura = await self.obter(fatura_id, usuario_id)
        if fatura.status != StatusFatura.ABERTA:
            raise ConflictError(
                f"Fatura não pode ser fechada (status atual: {fatura.status})."
            )
        fatura.status = StatusFatura.FECHADA
        logger.info("fatura_fechada", fatura_id=str(fatura_id))
        return fatura

    async def reabrir_fatura(self, fatura_id: uuid.UUID, usuario_id: uuid.UUID) -> Fatura:
        fatura = await self.obter(fatura_id, usuario_id)
        if fatura.status != StatusFatura.FECHADA:
            raise ConflictError(
                f"Fatura não pode ser reaberta (status atual: {fatura.status})."
            )
        fatura.status = StatusFatura.ABERTA
        logger.info("fatura_reaberta", fatura_id=str(fatura_id))
        return fatura

    async def registrar_pagamento(
        self,
        fatura_id: uuid.UUID,
        data: FaturaPagamentoCreate,
        usuario_id: uuid.UUID,
    ) -> Fatura:
        fatura = await self.obter(fatura_id, usuario_id)
        if fatura.status == StatusFatura.PAGA:
            raise ConflictError("Fatura já está paga.")
        if fatura.status == StatusFatura.ABERTA:
            raise DomainError("Feche a fatura antes de registrar o pagamento.")

        conta_pag = await self._conta_repo.get_by_id(data.conta_pagamento_id)
        if conta_pag is None:
            raise NotFoundError("Conta de pagamento não encontrada.")
        if conta_pag.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso à conta de pagamento.")
        if conta_pag.tipo == TipoConta.CARTAO_CREDITO:
            raise DomainError("Não é possível usar um cartão de crédito para pagar a fatura.")

        fatura.valor_pago = data.valor_pago
        fatura.data_pagamento = data.data_pagamento
        fatura.conta_pagamento_id = data.conta_pagamento_id
        fatura.status = StatusFatura.PAGA
        logger.info(
            "fatura_paga",
            fatura_id=str(fatura_id),
            valor_pago=str(data.valor_pago),
        )
        return fatura

    async def delta_valor_total(
        self, fatura_id: uuid.UUID, delta: Decimal
    ) -> None:
        """Chamado pelo módulo de lançamentos ao vincular/desvincular compras."""
        await self._repo.delta_valor_total(fatura_id, delta)
