import calendar
import uuid
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.core.utils import new_uuid
from app.modules.categoria.models import Categoria as CategoriaModel
from app.modules.categoria.repository import CategoriaRepository
from app.modules.conta_bancaria.models import TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.contato.models import Contato as ContatoModel, EscopoContato, TipoContato
from app.modules.contato.repository import ContatoRepository
from app.modules.empresa.repository import EmpresaRepository
from app.modules.fatura.service import FaturaService
from app.modules.lancamento.models import (
    FrequenciaRecorrencia,
    Lancamento,
    StatusLancamento,
)
from app.modules.lancamento.repository import LancamentoRepository
from app.modules.lancamento.schemas import (
    LancamentoBaixaCreate,
    LancamentoCreate,
    LancamentoParceladoCreate,
    LancamentoRecorrenteCreate,
    LancamentoUpdate,
)

logger = structlog.get_logger()

_CENTAVO = Decimal("0.01")


def _add_meses(d: date, meses: int) -> date:
    """Soma `meses` a uma data com clamping para o último dia do mês destino."""
    mes_total = d.month + meses
    ano = d.year + (mes_total - 1) // 12
    mes = (mes_total - 1) % 12 + 1
    ultimo = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(d.day, ultimo))


def _avancar(d: date, frequencia: FrequenciaRecorrencia, n: int) -> date:
    if frequencia == FrequenciaRecorrencia.SEMANAL:
        return d + timedelta(weeks=n)
    if frequencia == FrequenciaRecorrencia.QUINZENAL:
        return d + timedelta(weeks=2 * n)
    if frequencia == FrequenciaRecorrencia.MENSAL:
        return _add_meses(d, n)
    return _add_meses(d, n * 12)  # ANUAL


def _dividir_valor(total: Decimal, n: int) -> list[Decimal]:
    """Divide total em n parcelas (centavo extra na última)."""
    parcela = (total / n).quantize(_CENTAVO, rounding=ROUND_DOWN)
    resto = total - parcela * n
    valores = [parcela] * n
    valores[-1] += resto
    return valores


class LancamentoService:
    def __init__(
        self,
        repo: LancamentoRepository,
        conta_repo: ContaBancariaRepository,
        fatura_svc: FaturaService,
        categoria_repo: CategoriaRepository | None = None,
        contato_repo: ContatoRepository | None = None,
        empresa_repo: EmpresaRepository | None = None,
    ) -> None:
        self._repo = repo
        self._conta_repo = conta_repo
        self._fatura_svc = fatura_svc
        self._categoria_repo = categoria_repo
        self._contato_repo = contato_repo
        self._empresa_repo = empresa_repo

    # ──────────────────────────────────────────────────────────────────────────
    # Leitura
    # ──────────────────────────────────────────────────────────────────────────

    async def listar(self, usuario_id: uuid.UUID, **filtros: object) -> list[Lancamento]:
        return await self._repo.listar(usuario_id, **filtros)  # type: ignore[arg-type]

    async def obter(self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID) -> Lancamento:
        lct = await self._repo.get_by_id(lancamento_id)
        if lct is None:
            raise NotFoundError("Lançamento não encontrado.")
        if lct.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a este lançamento.")
        return lct

    # ──────────────────────────────────────────────────────────────────────────
    # Criação
    # ──────────────────────────────────────────────────────────────────────────

    async def criar_simples(
        self, data: LancamentoCreate, usuario_id: uuid.UUID
    ) -> Lancamento:
        fatura_id = await self._resolver_fatura(
            data.conta_bancaria_id, data.data_competencia, usuario_id
        )
        lct = Lancamento(
            empresa_id=data.empresa_id,
            usuario_id=usuario_id,
            tipo=data.tipo,
            descricao=data.descricao,
            valor=data.valor,
            valor_pago=Decimal("0"),
            data_competencia=data.data_competencia,
            data_vencimento=data.data_vencimento,
            status=StatusLancamento.PENDENTE,
            categoria_id=data.categoria_id,
            contato_id=data.contato_id,
            conta_bancaria_id=data.conta_bancaria_id,
            fatura_id=fatura_id,
            observacoes=data.observacoes,
        )
        await self._repo.create(lct)
        if fatura_id is not None:
            await self._fatura_svc.delta_valor_total(fatura_id, data.valor)
        await self._repo.commit()
        await self._repo.refresh(lct)
        logger.info(
            "lancamento_criado",
            tipo=data.tipo,
            valor=str(data.valor),
            empresa_id=str(data.empresa_id),
        )
        return lct

    async def criar_parcelado(
        self, data: LancamentoParceladoCreate, usuario_id: uuid.UUID
    ) -> list[Lancamento]:
        grupo_id = new_uuid()
        valores = _dividir_valor(data.valor_total, data.parcelas)
        lancamentos: list[Lancamento] = []

        for i in range(data.parcelas):
            competencia = _add_meses(data.data_primeira_competencia, i)
            vencimento = _add_meses(data.data_primeiro_vencimento, i)
            fatura_id = await self._resolver_fatura(
                data.conta_bancaria_id, competencia, usuario_id
            )
            lct = Lancamento(
                empresa_id=data.empresa_id,
                usuario_id=usuario_id,
                tipo=data.tipo,
                descricao=f"{data.descricao} ({i + 1}/{data.parcelas})",
                valor=valores[i],
                valor_pago=Decimal("0"),
                data_competencia=competencia,
                data_vencimento=vencimento,
                status=StatusLancamento.PENDENTE,
                categoria_id=data.categoria_id,
                contato_id=data.contato_id,
                conta_bancaria_id=data.conta_bancaria_id,
                fatura_id=fatura_id,
                numero_parcela=i + 1,
                total_parcelas=data.parcelas,
                grupo_parcelas_id=grupo_id,
                observacoes=data.observacoes,
            )
            lancamentos.append(lct)

        await self._repo.create_many(lancamentos)
        for lct in lancamentos:
            if lct.fatura_id is not None:
                await self._fatura_svc.delta_valor_total(lct.fatura_id, lct.valor)
        await self._repo.commit()
        logger.info(
            "lancamento_parcelado_criado",
            parcelas=data.parcelas,
            total=str(data.valor_total),
            grupo_id=str(grupo_id),
        )
        return lancamentos

    async def criar_recorrente(
        self, data: LancamentoRecorrenteCreate, usuario_id: uuid.UUID
    ) -> list[Lancamento]:
        recorrencia_id = new_uuid()
        lancamentos: list[Lancamento] = []

        for i in range(data.quantidade):
            competencia = _avancar(data.data_primeira_competencia, data.frequencia, i)
            vencimento = _avancar(data.data_primeiro_vencimento, data.frequencia, i)
            fatura_id = await self._resolver_fatura(
                data.conta_bancaria_id, competencia, usuario_id
            )
            lct = Lancamento(
                empresa_id=data.empresa_id,
                usuario_id=usuario_id,
                tipo=data.tipo,
                descricao=data.descricao,
                valor=data.valor,
                valor_pago=Decimal("0"),
                data_competencia=competencia,
                data_vencimento=vencimento,
                status=StatusLancamento.PENDENTE,
                categoria_id=data.categoria_id,
                contato_id=data.contato_id,
                conta_bancaria_id=data.conta_bancaria_id,
                fatura_id=fatura_id,
                recorrencia_id=recorrencia_id,
                observacoes=data.observacoes,
            )
            lancamentos.append(lct)

        await self._repo.create_many(lancamentos)
        for lct in lancamentos:
            if lct.fatura_id is not None:
                await self._fatura_svc.delta_valor_total(lct.fatura_id, lct.valor)
        await self._repo.commit()
        logger.info(
            "lancamento_recorrente_criado",
            quantidade=data.quantidade,
            frequencia=data.frequencia,
            recorrencia_id=str(recorrencia_id),
        )
        return lancamentos

    # ──────────────────────────────────────────────────────────────────────────
    # Operações
    # ──────────────────────────────────────────────────────────────────────────

    async def atualizar(
        self, lancamento_id: uuid.UUID, data: LancamentoUpdate, usuario_id: uuid.UUID
    ) -> Lancamento:
        lct = await self.obter(lancamento_id, usuario_id)
        if lct.status == StatusLancamento.CANCELADO:
            raise DomainError("Não é possível editar um lançamento cancelado.")
        if lct.status == StatusLancamento.PAGO:
            raise DomainError("Não é possível editar um lançamento já pago.")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lct, field, value)
        await self._repo.commit()
        await self._repo.refresh(lct)
        return lct

    async def registrar_baixa(
        self,
        lancamento_id: uuid.UUID,
        data: LancamentoBaixaCreate,
        usuario_id: uuid.UUID,
    ) -> Lancamento:
        lct = await self.obter(lancamento_id, usuario_id)

        if lct.status == StatusLancamento.CANCELADO:
            raise DomainError("Não é possível registrar baixa em lançamento cancelado.")
        if lct.status == StatusLancamento.PAGO:
            raise ConflictError("Lançamento já está totalmente pago.")
        if lct.fatura_id is not None:
            raise DomainError(
                "Lançamentos vinculados a fatura de cartão são liquidados pelo pagamento da fatura."
            )

        conta = await self._conta_repo.get_by_id(data.conta_bancaria_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")
        if conta.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso à conta bancária.")

        if self._categoria_repo is not None:
            categoria = await self._categoria_repo.get_by_id(data.categoria_id)
            if categoria is None:
                raise NotFoundError("Categoria não encontrada.")
            if categoria.usuario_id != usuario_id:
                raise PermissionDeniedError("Sem acesso à categoria.")

        saldo_restante = lct.valor - lct.valor_pago
        if data.valor_pago > saldo_restante:
            raise DomainError(
                f"Valor pago ({data.valor_pago}) excede o saldo restante ({saldo_restante})."
            )

        lct.valor_pago += data.valor_pago
        lct.data_pagamento = data.data_pagamento
        lct.conta_bancaria_id = data.conta_bancaria_id
        lct.categoria_id = data.categoria_id

        if lct.valor_pago >= lct.valor:
            lct.status = StatusLancamento.PAGO
            logger.info("lancamento_pago", lancamento_id=str(lancamento_id))
        else:
            logger.info(
                "lancamento_baixa_parcial",
                lancamento_id=str(lancamento_id),
                valor_pago=str(lct.valor_pago),
            )
        await self._repo.commit()
        await self._repo.refresh(lct)
        return lct

    async def cancelar(self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID) -> Lancamento:
        lct = await self.obter(lancamento_id, usuario_id)
        if lct.status == StatusLancamento.CANCELADO:
            raise ConflictError("Lançamento já está cancelado.")
        if lct.status == StatusLancamento.PAGO:
            raise DomainError("Não é possível cancelar um lançamento já pago.")

        lct.status = StatusLancamento.CANCELADO
        lct.ativo = False

        if lct.fatura_id is not None:
            await self._fatura_svc.delta_valor_total(lct.fatura_id, -lct.valor)

        logger.info("lancamento_cancelado", lancamento_id=str(lancamento_id))
        await self._repo.commit()
        await self._repo.refresh(lct)
        return lct

    async def importar_linhas(
        self,
        empresa_id: uuid.UUID,
        tipo: TipoLancamento | None,
        linhas: list[dict[str, object]],
        usuario_id: uuid.UUID,
    ) -> int:
        importadas = 0
        _cat_cache: dict[str, uuid.UUID] = {}
        _cont_cache: dict[str, uuid.UUID] = {}

        for item in linhas:
            if not item["valida"]:
                continue
            payload = item["payload"]

            row_empresa_id = empresa_id
            if empresa_nome := _to_str_or_none(payload.get("col_empresa")):
                if self._empresa_repo is None:
                    raise DomainError("Repositório de empresa não configurado para importação.")
                empresa = await self._empresa_repo.get_by_nome(empresa_nome, usuario_id)
                if empresa is None:
                    continue
                row_empresa_id = empresa.id

            row_tipo = tipo
            if col_tipo := _to_str_or_none(payload.get("col_tipo")):
                row_tipo = TipoLancamento.DESPESA if col_tipo == "CAP" else TipoLancamento.RECEITA
            if row_tipo is None:
                continue

            cat_id = _to_uuid_or_none(payload.get("categoria_id"))
            if cat_id is None:
                if cat_nome := _to_str_or_none(payload.get("categoria_nome")):
                    cache_key = f"{row_tipo}:{cat_nome.lower()}"
                    if cache_key in _cat_cache:
                        cat_id = _cat_cache[cache_key]
                    else:
                        cat_id = await self._resolver_categoria_por_nome(cat_nome, row_tipo, usuario_id)
                        _cat_cache[cache_key] = cat_id

            cont_id = _to_uuid_or_none(payload.get("contato_id"))
            if cont_id is None:
                if cont_nome := _to_str_or_none(payload.get("contato_nome")):
                    cont_nome_lower = cont_nome.lower()
                    if cont_nome_lower in _cont_cache:
                        cont_id = _cont_cache[cont_nome_lower]
                    else:
                        cont_id = await self._resolver_contato_por_nome(cont_nome, usuario_id)
                        _cont_cache[cont_nome_lower] = cont_id

            await self._validar_ids_importacao(
                payload.get("categoria_id"),
                payload.get("contato_id"),
                payload.get("conta_bancaria_id"),
                usuario_id,
                row_empresa_id,
            )

            data = LancamentoCreate(
                empresa_id=row_empresa_id,
                tipo=row_tipo,
                descricao=str(payload["descricao"]),
                valor=payload["valor"],
                data_competencia=payload["data_competencia"],
                data_vencimento=payload["data_vencimento"],
                categoria_id=cat_id,
                contato_id=cont_id,
                conta_bancaria_id=_to_uuid_or_none(payload.get("conta_bancaria_id")),
                observacoes=_to_str_or_none(payload.get("observacoes")),
            )
            await self.criar_simples(data, usuario_id)
            importadas += 1
        return importadas

    async def _resolver_categoria_por_nome(
        self, nome: str, tipo: TipoLancamento, usuario_id: uuid.UUID
    ) -> uuid.UUID:
        if self._categoria_repo is None:
            raise DomainError("Repositório de categoria não configurado para importação.")
        categoria = await self._categoria_repo.get_by_nome(nome, str(tipo), usuario_id)
        if categoria is not None:
            return categoria.id
        nova = CategoriaModel(
            usuario_id=usuario_id,
            nome=nome,
            tipo=str(tipo),
            escopo="global",
            nivel=1,
        )
        await self._categoria_repo.create(nova)
        return nova.id

    async def _resolver_contato_por_nome(self, nome: str, usuario_id: uuid.UUID) -> uuid.UUID:
        if self._contato_repo is None:
            raise DomainError("Repositório de contato não configurado para importação.")
        contato = await self._contato_repo.get_by_nome(nome, usuario_id)
        if contato is not None:
            return contato.id
        novo = ContatoModel(
            usuario_id=usuario_id,
            tipo=TipoContato.PJ,
            documento=None,
            nome_principal=nome,
            eh_cliente=True,
            eh_fornecedor=True,
            escopo=EscopoContato.GLOBAL,
        )
        await self._contato_repo.create(novo)
        return novo.id

    # ──────────────────────────────────────────────────────────────────────────
    # Internos
    # ──────────────────────────────────────────────────────────────────────────

    async def _resolver_fatura(
        self,
        conta_bancaria_id: uuid.UUID | None,
        competencia: date,
        usuario_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Retorna fatura_id se a conta for cartão de crédito; None caso contrário."""
        if conta_bancaria_id is None:
            return None
        conta = await self._conta_repo.get_by_id(conta_bancaria_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")
        if conta.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso à conta bancária.")
        if conta.tipo != TipoConta.CARTAO_CREDITO:
            return None
        fatura = await self._fatura_svc.obter_ou_criar_fatura_aberta(
            conta_bancaria_id, competencia, usuario_id
        )
        return fatura.id

    async def _validar_ids_importacao(
        self,
        categoria_id: object,
        contato_id: object,
        conta_bancaria_id: object,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID,
    ) -> None:
        categoria_uuid = _to_uuid_or_none(categoria_id)
        if categoria_id is not None and categoria_uuid is None:
            raise DomainError("Categoria deve ser informada como UUID válido.")
        if categoria_uuid is not None:
            if self._categoria_repo is None:
                raise DomainError("Repositório de categoria não configurado para importação.")
            categoria = await self._categoria_repo.get_by_id(categoria_uuid)
            if categoria is None:
                raise DomainError("Categoria informada não foi encontrada.")
            if categoria.usuario_id != usuario_id:
                raise PermissionDeniedError("Sem acesso à categoria informada.")
            if categoria.empresa_id is not None and categoria.empresa_id != empresa_id:
                raise DomainError("Categoria não pertence à empresa selecionada.")

        contato_uuid = _to_uuid_or_none(contato_id)
        if contato_id is not None and contato_uuid is None:
            raise DomainError("Contato deve ser informado como UUID válido.")
        if contato_uuid is not None:
            if self._contato_repo is None:
                raise DomainError("Repositório de contato não configurado para importação.")
            contato = await self._contato_repo.get_by_id(contato_uuid)
            if contato is None:
                raise DomainError("Contato informado não foi encontrado.")
            if contato.usuario_id != usuario_id:
                raise PermissionDeniedError("Sem acesso ao contato informado.")
            if contato.empresa_id is not None and contato.empresa_id != empresa_id:
                raise DomainError("Contato não pertence à empresa selecionada.")

        conta_uuid = _to_uuid_or_none(conta_bancaria_id)
        if conta_bancaria_id is not None and conta_uuid is None:
            raise DomainError("Conta bancária deve ser informada como UUID válido.")


def _to_uuid_or_none(valor: object) -> uuid.UUID | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, uuid.UUID):
        return valor
    try:
        return uuid.UUID(str(valor))
    except (ValueError, TypeError):
        return None


def _to_str_or_none(valor: object) -> str | None:
    if valor in (None, ""):
        return None
    return str(valor)
