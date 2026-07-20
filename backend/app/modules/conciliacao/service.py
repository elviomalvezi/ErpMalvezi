import re
import uuid
from decimal import Decimal

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conciliacao.models import (
    ImportacaoBancaria,
    RegraCategorizacao,
    StatusImportacao,
    StatusTransacao,
    TipoTransacao,
    TransacaoBancaria,
)
from app.modules.conciliacao.parser import parse_csv, parse_ofx
from app.modules.conciliacao.repository import ConciliacaoRepository
from app.modules.conciliacao.schemas import ConfigCSV, CriarLancamentoRequest
from app.modules.conta_bancaria.models import TipoConta
from app.modules.conta_bancaria.repository import ContaBancariaRepository
from app.modules.lancamento.models import Lancamento, StatusLancamento
from app.modules.lancamento.repository import LancamentoRepository

_NORMALIZAR_RE = re.compile(r"[^a-z0-9\s]")


def _normalizar_padrao(texto: str) -> str:
    texto = texto.lower()
    texto = _NORMALIZAR_RE.sub(" ", texto)
    return " ".join(texto.split())[:300]


class ConciliacaoService:
    def __init__(
        self,
        repo: ConciliacaoRepository,
        conta_repo: ContaBancariaRepository,
        lancamento_repo: LancamentoRepository,
    ) -> None:
        self._repo = repo
        self._conta_repo = conta_repo
        self._lancamento_repo = lancamento_repo

    async def _get_conta_validada(
        self, conta_id: uuid.UUID, usuario_id: uuid.UUID
    ):  # type: ignore[return]
        conta = await self._conta_repo.get_by_id(conta_id)
        if conta is None:
            raise NotFoundError("Conta bancária não encontrada.")
        if not await self._conta_repo.tem_acesso(conta_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a esta conta bancária.")
        if conta.tipo == TipoConta.CARTAO_CREDITO:
            raise DomainError("Não é possível importar extrato de cartão de crédito.")
        return conta

    async def importar_ofx(
        self,
        content: bytes,
        nome_arquivo: str,
        conta_id: uuid.UUID,
        empresa_id: uuid.UUID,
        usuario_id: uuid.UUID,
    ) -> ImportacaoBancaria:
        conta = await self._get_conta_validada(conta_id, usuario_id)

        try:
            entradas = parse_ofx(content)
        except Exception as exc:
            raise DomainError(f"Erro ao processar arquivo OFX: {exc}") from exc

        return await self._salvar_importacao(
            entradas, nome_arquivo, conta, empresa_id, usuario_id
        )

    async def importar_csv(
        self,
        content: bytes,
        nome_arquivo: str,
        conta_id: uuid.UUID,
        empresa_id: uuid.UUID,
        usuario_id: uuid.UUID,
        config: ConfigCSV | None = None,
    ) -> ImportacaoBancaria:
        conta = await self._get_conta_validada(conta_id, usuario_id)
        cfg = config or ConfigCSV()

        try:
            entradas = parse_csv(
                content,
                delimiter=cfg.delimiter,
                col_data=cfg.col_data,
                col_descricao=cfg.col_descricao,
                col_valor=cfg.col_valor,
                decimal_sep=cfg.decimal_sep,
                formato_data=cfg.formato_data,
                col_tipo=cfg.col_tipo,
                encoding=cfg.encoding,
                skip_header=cfg.skip_header,
            )
        except Exception as exc:
            raise DomainError(f"Erro ao processar arquivo CSV: {exc}") from exc

        return await self._salvar_importacao(
            entradas, nome_arquivo, conta, empresa_id, usuario_id
        )

    async def _salvar_importacao(
        self,
        entradas: list[dict],
        nome_arquivo: str,
        conta,  # ContaBancaria
        empresa_id: uuid.UUID,
        usuario_id: uuid.UUID,
    ) -> ImportacaoBancaria:
        # A empresa é derivada da conta já validada (ignora o valor enviado pelo
        # cliente), impedindo gravar a importação em empresa sem acesso.
        empresa_id = conta.empresa_id
        importacao = ImportacaoBancaria(
            conta_bancaria_id=conta.id,
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            nome_arquivo=nome_arquivo[:200],
            status=StatusImportacao.CONCLUIDA,
            total_transacoes=0,
            conciliadas=0,
            ignoradas=0,
        )
        await self._repo.create_importacao(importacao)

        transacoes: list[TransacaoBancaria] = []
        for entrada in entradas:
            id_externo = entrada.get("id_externo")
            if id_externo and await self._repo.id_externo_existe(conta.id, id_externo):
                continue
            tipo = TipoTransacao(entrada["tipo"])
            t = TransacaoBancaria(
                importacao_id=importacao.id,
                conta_bancaria_id=conta.id,
                empresa_id=empresa_id,
                usuario_id=usuario_id,
                id_externo=id_externo,
                data=entrada["data"],
                valor=Decimal(str(entrada["valor"])),
                tipo=tipo,
                descricao_original=entrada["descricao"],
                status=StatusTransacao.PENDENTE,
                lancamento_id=None,
            )
            transacoes.append(t)

        if transacoes:
            await self._repo.create_transacoes(transacoes)

        importacao.total_transacoes = len(transacoes)
        await self._repo.commit()
        return importacao

    async def listar_importacoes(
        self,
        usuario_id: uuid.UUID,
        conta_bancaria_id: uuid.UUID | None = None,
    ) -> list[ImportacaoBancaria]:
        return await self._repo.listar_importacoes(usuario_id, conta_bancaria_id)

    async def listar_transacoes(
        self,
        importacao_id: uuid.UUID,
        usuario_id: uuid.UUID,
        status: StatusTransacao | None = None,
    ) -> list[TransacaoBancaria]:
        importacao = await self._repo.get_importacao(importacao_id)
        if importacao is None:
            raise NotFoundError("Importação não encontrada.")
        if not await self._repo.tem_acesso_empresa(importacao.empresa_id, usuario_id):
            raise PermissionDeniedError("Sem permissão para esta importação.")
        return await self._repo.listar_transacoes(importacao_id, status)

    async def sugerir_match(
        self, transacao_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> list[Lancamento]:
        transacao = await self._get_transacao_validada(transacao_id, usuario_id)
        if transacao.status != StatusTransacao.PENDENTE:
            raise DomainError("Transação já foi conciliada ou ignorada.")
        return await self._repo.buscar_lancamentos_para_match(
            transacao.conta_bancaria_id, usuario_id, transacao.data, transacao.valor
        )

    async def conciliar(
        self, transacao_id: uuid.UUID, lancamento_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> TransacaoBancaria:
        transacao = await self._get_transacao_validada(transacao_id, usuario_id)
        if transacao.status != StatusTransacao.PENDENTE:
            raise ConflictError("Transação já está conciliada ou ignorada.")

        lancamento = await self._lancamento_repo.get_by_id(lancamento_id)
        if lancamento is None:
            raise NotFoundError("Lançamento não encontrado.")
        if not await self._lancamento_repo.tem_acesso(lancamento_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a este lançamento.")
        if lancamento.empresa_id != transacao.empresa_id:
            raise DomainError("O lançamento deve pertencer à mesma empresa da transação.")

        transacao.status = StatusTransacao.CONCILIADA
        transacao.lancamento_id = lancamento_id
        await self._repo.commit()
        return transacao

    async def criar_lancamento_de_transacao(
        self,
        transacao_id: uuid.UUID,
        data: CriarLancamentoRequest,
        usuario_id: uuid.UUID,
    ) -> TransacaoBancaria:
        transacao = await self._get_transacao_validada(transacao_id, usuario_id)
        if transacao.status != StatusTransacao.PENDENTE:
            raise ConflictError("Transação já está conciliada ou ignorada.")

        lancamento = Lancamento(
            # empresa derivada da transação validada (não do payload do cliente).
            empresa_id=transacao.empresa_id,
            usuario_id=usuario_id,
            tipo=data.tipo,
            descricao=data.descricao,
            valor=transacao.valor,
            valor_pago=Decimal("0"),
            data_competencia=data.data_competencia,
            data_vencimento=data.data_vencimento,
            status=StatusLancamento.PENDENTE,
            categoria_id=data.categoria_id,
            contato_id=data.contato_id,
            conta_bancaria_id=transacao.conta_bancaria_id,
            observacoes=data.observacoes,
            ativo=True,
        )
        await self._lancamento_repo.create(lancamento)

        transacao.status = StatusTransacao.CONCILIADA
        transacao.lancamento_id = lancamento.id

        if data.categoria_id is not None:
            padrao = _normalizar_padrao(transacao.descricao_original)
            if padrao:
                await self._repo.upsert_regra(
                    usuario_id=usuario_id,
                    padrao=padrao,
                    categoria_id=data.categoria_id,
                    tipo_lancamento=data.tipo,
                    contato_id=data.contato_id,
                )

        await self._repo.commit()
        return transacao

    async def ignorar(
        self, transacao_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> TransacaoBancaria:
        transacao = await self._get_transacao_validada(transacao_id, usuario_id)
        if transacao.status != StatusTransacao.PENDENTE:
            raise ConflictError("Transação já está conciliada ou ignorada.")
        transacao.status = StatusTransacao.IGNORADA
        await self._repo.commit()
        return transacao

    async def sugerir_categoria(
        self, transacao_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> RegraCategorizacao | None:
        transacao = await self._get_transacao_validada(transacao_id, usuario_id)
        padrao = _normalizar_padrao(transacao.descricao_original)
        if not padrao:
            return None
        return await self._repo.buscar_regra(usuario_id, padrao)

    async def _get_transacao_validada(
        self, transacao_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> TransacaoBancaria:
        transacao = await self._repo.get_transacao(transacao_id)
        if transacao is None:
            raise NotFoundError("Transação não encontrada.")
        if not await self._repo.tem_acesso_empresa(transacao.empresa_id, usuario_id):
            raise PermissionDeniedError("Sem permissão para esta transação.")
        return transacao
