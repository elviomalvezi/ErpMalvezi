import calendar
import uuid
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.core.utils import new_uuid
from app.modules.categoria.models import Categoria as CategoriaModel
from app.modules.categoria.repository import CategoriaRepository
from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.contato.models import Contato as ContatoModel
from app.modules.contato.models import EscopoContato, TipoContato
from app.modules.contato.repository import ContatoRepository
from app.modules.empresa.models import Empresa, TipoPessoa, UsuarioEmpresa
from app.modules.empresa.repository import EmpresaRepository
from app.modules.fatura.service import FaturaService
from app.modules.lancamento.models import (
    FrequenciaRecorrencia,
    Lancamento,
    StatusLancamento,
    TipoLancamento,
)
from app.modules.lancamento.repository import LancamentoRepository
from app.modules.lancamento.schemas import (
    ExtratoItemResponse,
    ExtratoResponse,
    LancamentoBaixaCreate,
    LancamentoCreate,
    LancamentoParceladoCreate,
    LancamentoRecorrenteCreate,
    LancamentoResponse,
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

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        tipo: TipoLancamento | None = None,
        status: StatusLancamento | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        categoria_id: uuid.UUID | None = None,
        contato_id: uuid.UUID | None = None,
        conta_bancaria_id: uuid.UUID | None = None,
        grupo_parcelas_id: uuid.UUID | None = None,
        recorrencia_id: uuid.UUID | None = None,
        apenas_ativos: bool = True,
        descricao: str | None = None,
        limit: int | None = None,
    ) -> list[Lancamento]:
        return await self._repo.listar(
            usuario_id,
            empresa_id=empresa_id,
            tipo=tipo,
            status=status,
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

    async def obter(self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID) -> Lancamento:
        lct = await self._repo.get_by_id(lancamento_id)
        if lct is None:
            raise NotFoundError("Lançamento não encontrado.")
        if not await self._repo.tem_acesso(lancamento_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a este lançamento.")
        return lct

    async def extrato(
        self,
        conta_bancaria_id: uuid.UUID,
        usuario_id: uuid.UUID,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> ExtratoResponse:
        conta = await self._conta_repo.get_by_id(conta_bancaria_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")

        data_saldo_ini = conta.data_saldo_inicial if isinstance(conta.data_saldo_inicial, date) else None
        saldo_ant = await self._repo.saldo_anterior(
            conta_bancaria_id,
            usuario_id,
            ate=data_inicio,
            saldo_inicial=conta.saldo_inicial,
            data_saldo_inicial=data_saldo_ini,
        )
        lancamentos = await self._repo.listar_extrato(conta_bancaria_id, usuario_id, data_inicio, data_fim)

        saldo_corrente = saldo_ant
        itens: list[ExtratoItemResponse] = []
        for lct in lancamentos:
            if lct.status == StatusLancamento.PAGO:
                if lct.tipo == TipoLancamento.RECEITA:
                    saldo_corrente += lct.valor_pago
                else:
                    saldo_corrente -= lct.valor_pago
            itens.append(ExtratoItemResponse(
                lancamento=LancamentoResponse.model_validate(lct),
                saldo_apos=saldo_corrente,
            ))

        return ExtratoResponse(
            conta_bancaria_id=conta_bancaria_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            saldo_anterior=saldo_ant,
            saldo_final=saldo_corrente,
            itens=itens,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Criação
    # ──────────────────────────────────────────────────────────────────────────

    async def criar_simples(
        self, data: LancamentoCreate, usuario_id: uuid.UUID
    ) -> Lancamento:
        await self._validar_acesso_empresa(data.empresa_id, usuario_id)
        await self._validar_patrimonio_regras(data.categoria_id, data.veiculo_id, data.imovel_id)
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
            veiculo_id=data.veiculo_id,
            imovel_id=data.imovel_id,
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

        await self._validar_acesso_empresa(data.empresa_id, usuario_id)
        await self._validar_patrimonio_regras(data.categoria_id, getattr(data, 'veiculo_id', None), getattr(data, 'imovel_id', None))
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
                veiculo_id=getattr(data, 'veiculo_id', None),
                imovel_id=getattr(data, 'imovel_id', None),
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

        await self._validar_acesso_empresa(data.empresa_id, usuario_id)
        await self._validar_patrimonio_regras(data.categoria_id, getattr(data, 'veiculo_id', None), getattr(data, 'imovel_id', None))
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
                veiculo_id=getattr(data, 'veiculo_id', None),
                imovel_id=getattr(data, 'imovel_id', None),
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

        if self._categoria_repo is not None:
            categoria = await self._categoria_repo.get_by_id(data.categoria_id)
            if categoria is None:
                raise NotFoundError("Categoria não encontrada.")
            if not await self._categoria_repo.tem_acesso(data.categoria_id, usuario_id):
                raise PermissionDeniedError("Sem acesso à categoria.")

        # Permite registrar valor acima do previsto (ex.: pagamento/recebimento
        # maior que o valor previsto). Não há teto sobre o saldo restante.
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

    async def marcar_nao_realizado(
        self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> Lancamento:
        """Marca um previsto que comprovadamente não ocorreu.

        Diferente de cancelar: o lançamento permanece visível (ativo=True),
        mas sai do previsto e do realizado (status próprio).
        """
        lct = await self.obter(lancamento_id, usuario_id)
        if lct.status == StatusLancamento.NAO_REALIZADO:
            raise ConflictError("Lançamento já está marcado como não realizado.")
        if lct.status == StatusLancamento.PAGO:
            raise DomainError("Não é possível marcar como não realizado um lançamento já realizado.")
        if lct.status == StatusLancamento.CANCELADO:
            raise DomainError("Lançamento cancelado não pode ser marcado como não realizado.")
        if lct.valor_pago and lct.valor_pago > Decimal("0"):
            raise DomainError(
                "Lançamento com baixa parcial não pode ser marcado como não realizado. "
                "Estorne a baixa primeiro."
            )
        if lct.fatura_id is not None:
            raise DomainError(
                "Lançamentos vinculados a fatura de cartão não podem ser marcados como não realizados."
            )

        lct.status = StatusLancamento.NAO_REALIZADO
        logger.info("lancamento_nao_realizado", lancamento_id=str(lancamento_id))
        await self._repo.commit()
        await self._repo.refresh(lct)
        return lct

    async def reverter_para_previsto(
        self, lancamento_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> Lancamento:
        """Reverte um lançamento 'não realizado' de volta para previsto (pendente)."""
        lct = await self.obter(lancamento_id, usuario_id)
        if lct.status != StatusLancamento.NAO_REALIZADO:
            raise DomainError("Apenas lançamentos não realizados podem voltar para previsto.")

        lct.status = StatusLancamento.PENDENTE
        logger.info("lancamento_revertido_previsto", lancamento_id=str(lancamento_id))
        await self._repo.commit()
        await self._repo.refresh(lct)
        return lct

    async def duplicar(
        self,
        lancamento_id: uuid.UUID,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
    ) -> Lancamento:
        original = await self.obter(lancamento_id, usuario_id)

        empresa_destino = empresa_id or original.empresa_id
        mesma_empresa = empresa_destino == original.empresa_id
        if not mesma_empresa and (
            self._empresa_repo is None
            or (await self._empresa_repo.get_vinculo(usuario_id, empresa_destino)) is None
        ):
            raise PermissionDeniedError("Sem acesso à empresa de destino.")

        novo = Lancamento(
            id=new_uuid(),
            usuario_id=usuario_id,
            empresa_id=empresa_destino,
            tipo=original.tipo,
            descricao=f"Cópia de {original.descricao}",
            valor=original.valor,
            data_competencia=original.data_competencia,
            data_vencimento=original.data_vencimento,
            categoria_id=original.categoria_id,
            contato_id=original.contato_id,
            conta_bancaria_id=None,
            status=StatusLancamento.PENDENTE,
            observacoes=original.observacoes,
            tags=list(original.tags or []),
            veiculo_id=original.veiculo_id if mesma_empresa else None,
            imovel_id=original.imovel_id if mesma_empresa else None,
            ativo=True,
        )
        self._repo._db.add(novo)
        await self._repo.commit()
        await self._repo.refresh(novo)
        logger.info("lancamento_duplicado", original_id=str(lancamento_id), novo_id=str(novo.id))
        return novo

    async def importar_linhas(
        self,
        empresa_id: uuid.UUID,
        tipo: TipoLancamento | None,
        linhas: list[dict[str, object]],
        usuario_id: uuid.UUID,
    ) -> tuple[int, list[str]]:
        await self._validar_acesso_empresa(empresa_id, usuario_id)
        importadas = 0
        _empresas_criadas: set[str] = set()
        _empresa_cache: dict[str, uuid.UUID] = {}
        _cat_cache: dict[str, uuid.UUID] = {}
        _cont_cache: dict[str, uuid.UUID] = {}
        _conta_cache: dict[str, uuid.UUID] = {}

        # ── Passo 1: pré-criar todos os cadastros auxiliares e commitar ──────
        for item in linhas:
            if not item["valida"]:
                continue
            payload = item["payload"]

            row_empresa_id = empresa_id
            if empresa_nome := _to_str_or_none(payload.get("col_empresa")):
                row_empresa_id, criada = await self._resolver_empresa_por_nome(
                    empresa_nome, usuario_id, empresa_id, _empresa_cache
                )
                if criada:
                    _empresas_criadas.add(empresa_nome)

            row_tipo = tipo
            if col_tipo := _to_str_or_none(payload.get("col_tipo")):
                row_tipo = TipoLancamento.DESPESA if col_tipo == "CAP" else TipoLancamento.RECEITA
            if row_tipo is None:
                row_tipo = TipoLancamento.DESPESA

            if cat_nome := _to_str_or_none(payload.get("categoria_nome")):
                cache_key = f"{row_tipo}:{cat_nome.lower()}"
                if cache_key not in _cat_cache:
                    _cat_cache[cache_key] = await self._resolver_categoria_por_nome(cat_nome, row_tipo, usuario_id)

            if cont_nome := _to_str_or_none(payload.get("contato_nome")):
                # Cache por empresa+nome: o contato agora é exclusivo por empresa.
                cont_key = f"{row_empresa_id}:{cont_nome.lower()}"
                if cont_key not in _cont_cache:
                    _cont_cache[cont_key] = await self._resolver_contato_por_nome(
                        cont_nome, usuario_id, row_empresa_id
                    )

            if banco_nome := _to_str_or_none(payload.get("conta_banco")):
                agencia = _to_str_or_none(payload.get("conta_agencia"))
                numero_conta = _to_str_or_none(payload.get("conta_numero"))
                await self._resolver_conta_bancaria(
                    usuario_id, row_empresa_id, banco_nome, agencia, numero_conta, _conta_cache
                )

        # Commita todos os cadastros auxiliares antes dos lançamentos
        await self._repo.commit()

        # ── Passo 2: bulk insert dos lançamentos ──────────────────────────────
        for item in linhas:
            if not item["valida"]:
                continue
            payload = item["payload"]

            row_empresa_id = empresa_id
            if empresa_nome := _to_str_or_none(payload.get("col_empresa")):
                row_empresa_id, _ = await self._resolver_empresa_por_nome(
                    empresa_nome, usuario_id, empresa_id, _empresa_cache
                )

            row_tipo = tipo
            if col_tipo := _to_str_or_none(payload.get("col_tipo")):
                row_tipo = TipoLancamento.DESPESA if col_tipo == "CAP" else TipoLancamento.RECEITA
            if row_tipo is None:
                continue

            cat_id = _to_uuid_or_none(payload.get("categoria_id"))
            if cat_id is None and (cat_nome := _to_str_or_none(payload.get("categoria_nome"))):
                cache_key = f"{row_tipo}:{cat_nome.lower()}"
                if cache_key in _cat_cache:
                    cat_id = _cat_cache[cache_key]
                else:
                    cat_id = await self._resolver_categoria_por_nome(cat_nome, row_tipo, usuario_id)
                    _cat_cache[cache_key] = cat_id

            cont_id = _to_uuid_or_none(payload.get("contato_id"))
            if cont_id is None and (cont_nome := _to_str_or_none(payload.get("contato_nome"))):
                cont_key = f"{row_empresa_id}:{cont_nome.lower()}"
                if cont_key in _cont_cache:
                    cont_id = _cont_cache[cont_key]
                else:
                    cont_id = await self._resolver_contato_por_nome(
                        cont_nome, usuario_id, row_empresa_id
                    )
                    _cont_cache[cont_key] = cont_id

            # Resolver conta bancária por banco + agência + número
            conta_id = _to_uuid_or_none(payload.get("conta_bancaria_id"))
            if conta_id is None:
                banco_nome = _to_str_or_none(payload.get("conta_banco"))
                if banco_nome:
                    agencia = _to_str_or_none(payload.get("conta_agencia"))
                    numero_conta = _to_str_or_none(payload.get("conta_numero"))
                    conta_id = await self._resolver_conta_bancaria(
                        usuario_id, row_empresa_id, banco_nome, agencia, numero_conta, _conta_cache
                    )

            await self._validar_ids_importacao(
                payload.get("categoria_id"),
                payload.get("contato_id"),
                payload.get("conta_bancaria_id"),
                usuario_id,
                row_empresa_id,
            )

            # Acumula para inserção em lote
            lct = Lancamento(
                id=new_uuid(),
                usuario_id=usuario_id,
                empresa_id=row_empresa_id,
                tipo=row_tipo,
                descricao=str(payload["descricao"])[:300],  # trunca ao limite do campo
                valor=payload["valor"],
                data_competencia=payload["data_competencia"],
                data_vencimento=payload["data_vencimento"],
                categoria_id=cat_id,
                contato_id=cont_id,
                conta_bancaria_id=conta_id,
                observacoes=_to_str_or_none(payload.get("observacoes")),
                status=StatusLancamento.PENDENTE,
            )
            self._repo._db.add(lct)
            importadas += 1

            # Commit a cada 500 registros para não sobrecarregar a transação
            if importadas % 500 == 0:
                await self._repo.commit()

        # Commit final
        if importadas > 0:
            await self._repo.commit()

        return importadas, sorted(_empresas_criadas)

    async def _resolver_empresa_por_nome(
        self,
        nome: str,
        usuario_id: uuid.UUID,
        fallback_id: uuid.UUID,
        cache: dict[str, uuid.UUID],
    ) -> tuple[uuid.UUID, bool]:
        """Retorna (empresa_id, foi_criada). Cria empresa PF se não encontrada."""
        nome_lower = nome.lower()
        if nome_lower in cache:
            return cache[nome_lower], False

        if self._empresa_repo is not None:
            empresa = await self._empresa_repo.get_by_nome(nome, usuario_id)
            if empresa is not None:
                cache[nome_lower] = empresa.id
                return empresa.id, False

            # Cria empresa PF sem documento (a ser preenchido depois)
            nova = Empresa(
                tipo=TipoPessoa.PF,
                documento=None,
                nome_principal=nome,
                criado_por=usuario_id,
            )
            await self._empresa_repo.create(nova)
            vinculo = UsuarioEmpresa(usuario_id=usuario_id, empresa_id=nova.id)
            await self._empresa_repo.create_vinculo(vinculo)
            logger.info("empresa_criada_importacao", nome=nome, empresa_id=str(nova.id))
            cache[nome_lower] = nova.id
            return nova.id, True

        return fallback_id, False

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

    async def _resolver_contato_por_nome(
        self, nome: str, usuario_id: uuid.UUID, empresa_id: uuid.UUID
    ) -> uuid.UUID:
        """Resolve o fornecedor/cliente pelo nome DENTRO da empresa do lançamento.

        Reaproveita o contato específico da empresa (ou um global intencional);
        se não existir, cria um novo já vinculado à empresa.
        """
        if self._contato_repo is None:
            raise DomainError("Repositório de contato não configurado para importação.")
        contato = await self._contato_repo.get_by_nome_para_empresa(nome, usuario_id, empresa_id)
        if contato is not None:
            return contato.id
        novo = ContatoModel(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            tipo=TipoContato.PJ,
            documento=None,
            nome_principal=nome,
            eh_cliente=True,
            eh_fornecedor=True,
            escopo=EscopoContato.ESPECIFICO,
        )
        await self._contato_repo.create(novo)
        return novo.id

    async def _resolver_conta_bancaria(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID,
        banco: str,
        agencia: str | None,
        numero_conta: str | None,
        _cache: dict,
    ) -> uuid.UUID:
        cache_key = f"{empresa_id}|{banco}|{agencia}|{numero_conta}"
        if cache_key in _cache:
            return _cache[cache_key]

        conta = await self._conta_repo.get_by_dados_bancarios(
            usuario_id, empresa_id, banco, agencia, numero_conta
        )
        if conta is not None:
            _cache[cache_key] = conta.id
            return conta.id

        # Cria conta nova
        nome = f"{banco}"
        if agencia:
            nome += f" Ag.{agencia}"
        if numero_conta:
            nome += f" Cc.{numero_conta}"
        nova = ContaBancaria(
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            nome=nome,
            tipo=TipoConta.CORRENTE,
            banco=banco,
            agencia=agencia,
            numero_conta=numero_conta,
        )
        self._conta_repo._db.add(nova)
        await self._conta_repo._db.flush()
        _cache[cache_key] = nova.id
        logger.info("conta_bancaria_criada_importacao", banco=banco, agencia=agencia, numero_conta=numero_conta)
        return nova.id

    # ──────────────────────────────────────────────────────────────────────────
    # Internos
    # ──────────────────────────────────────────────────────────────────────────

    async def _validar_acesso_empresa(
        self, empresa_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> None:
        """Garante que o usuário pertence à empresa de destino do lançamento."""
        if self._empresa_repo is None:
            return
        if await self._empresa_repo.get_vinculo(usuario_id, empresa_id) is None:
            raise PermissionDeniedError("Sem acesso a esta empresa.")

    async def _validar_patrimonio_regras(
        self,
        categoria_id: uuid.UUID | None,
        veiculo_id: uuid.UUID | None,
        imovel_id: uuid.UUID | None,
    ) -> None:
        if categoria_id is None or self._categoria_repo is None:
            return
        cat = await self._categoria_repo.get_by_id(categoria_id)
        if cat is None:
            return
        if getattr(cat, "exigir_veiculo", False) and not veiculo_id:
            raise DomainError("Esta categoria exige a seleção de um veículo.")
        if getattr(cat, "exigir_imovel", False) and not imovel_id:
            raise DomainError("Esta categoria exige a seleção de um imóvel.")

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
            if not await self._categoria_repo.tem_acesso(categoria_uuid, usuario_id):
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
            if not await self._contato_repo.tem_acesso(contato_uuid, usuario_id):
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
