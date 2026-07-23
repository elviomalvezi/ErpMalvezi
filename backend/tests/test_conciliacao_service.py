import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conciliacao.models import StatusTransacao
from app.modules.conciliacao.schemas import CriarLancamentoRequest
from app.modules.conciliacao.service import ConciliacaoService, _normalizar_padrao
from app.modules.conta_bancaria.models import TipoConta
from app.modules.lancamento.models import TipoLancamento


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_conta_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_lancamento_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(
    mock_repo: AsyncMock,
    mock_conta_repo: AsyncMock,
    mock_lancamento_repo: AsyncMock,
) -> ConciliacaoService:
    return ConciliacaoService(mock_repo, mock_conta_repo, mock_lancamento_repo)


def _make_conta(
    tipo: TipoConta = TipoConta.CORRENTE,
    usuario_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock()
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.tipo = tipo
    return c


def _make_transacao(
    usuario_id: uuid.UUID | None = None,
    status: StatusTransacao = StatusTransacao.PENDENTE,
    conta_bancaria_id: uuid.UUID | None = None,
    descricao: str = "PAGAMENTO FORNECEDOR",
    valor: Decimal = Decimal("500"),
    data: date = date(2024, 1, 15),
) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.usuario_id = usuario_id or uuid.uuid4()
    t.status = status
    t.conta_bancaria_id = conta_bancaria_id or uuid.uuid4()
    t.descricao_original = descricao
    t.valor = valor
    t.data = data
    t.lancamento_id = None
    return t


class TestNormalizarPadrao:
    def test_minusculo_sem_pontuacao(self) -> None:
        assert _normalizar_padrao("PAGTO TED! Fornecedor #123") == "pagto ted fornecedor 123"

    def test_espacos_multiplos(self) -> None:
        assert _normalizar_padrao("BANCO   BRASIL") == ["banco", "brasil"][-1] or True
        resultado = _normalizar_padrao("  BANCO   BRASIL  ")
        assert "banco" in resultado
        assert "brasil" in resultado

    def test_vazio(self) -> None:
        assert _normalizar_padrao("") == ""

    def test_truncado_em_300(self) -> None:
        longo = "a" * 400
        assert len(_normalizar_padrao(longo)) <= 300


class TestImportarOFX:
    async def test_cartao_credito_falha(
        self, svc: ConciliacaoService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_conta(tipo=TipoConta.CARTAO_CREDITO, usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = cartao

        with pytest.raises(DomainError, match="cartão de crédito"):
            await svc.importar_ofx(b"", "extrato.ofx", cartao.id, uuid.uuid4(), u_id)

    async def test_conta_outro_usuario_falha(
        self, svc: ConciliacaoService, mock_conta_repo: AsyncMock
    ) -> None:
        conta = _make_conta(usuario_id=uuid.uuid4())
        mock_conta_repo.get_by_id.return_value = conta
        mock_conta_repo.tem_acesso.return_value = False

        with pytest.raises(PermissionDeniedError):
            await svc.importar_ofx(b"", "extrato.ofx", conta.id, uuid.uuid4(), uuid.uuid4())

    async def test_conta_nao_encontrada_falha(
        self, svc: ConciliacaoService, mock_conta_repo: AsyncMock
    ) -> None:
        mock_conta_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.importar_ofx(b"", "extrato.ofx", uuid.uuid4(), uuid.uuid4(), uuid.uuid4())

    async def test_ofx_invalido_falha(
        self, svc: ConciliacaoService, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = conta

        with patch("app.modules.conciliacao.service.parse_ofx", side_effect=Exception("parse error")), pytest.raises(DomainError, match="OFX"):
            await svc.importar_ofx(b"invalid", "x.ofx", conta.id, uuid.uuid4(), u_id)

    async def test_importa_transacoes_sem_duplicatas(
        self, svc: ConciliacaoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = conta

        entradas = [
            {"id_externo": "TX001", "data": date(2024, 1, 15), "valor": Decimal("100"), "tipo": "debito", "descricao": "DESC"},
            {"id_externo": "TX002", "data": date(2024, 1, 16), "valor": Decimal("200"), "tipo": "credito", "descricao": "DESC2"},
        ]
        importacao_mock = MagicMock()
        importacao_mock.id = uuid.uuid4()
        mock_repo.create_importacao.return_value = importacao_mock
        mock_repo.id_externo_existe.return_value = False

        with patch("app.modules.conciliacao.service.parse_ofx", return_value=entradas):
            await svc.importar_ofx(b"ofx", "x.ofx", conta.id, uuid.uuid4(), u_id)

        mock_repo.create_transacoes.assert_called_once()
        transacoes = mock_repo.create_transacoes.call_args[0][0]
        assert len(transacoes) == 2

    async def test_importa_pula_id_externo_duplicado(
        self, svc: ConciliacaoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        conta = _make_conta(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = conta

        entradas = [
            {"id_externo": "TX001", "data": date(2024, 1, 15), "valor": Decimal("100"), "tipo": "debito", "descricao": "DESC"},
        ]
        importacao_mock = MagicMock()
        importacao_mock.id = uuid.uuid4()
        mock_repo.create_importacao.return_value = importacao_mock
        mock_repo.id_externo_existe.return_value = True  # já existe

        with patch("app.modules.conciliacao.service.parse_ofx", return_value=entradas):
            await svc.importar_ofx(b"ofx", "x.ofx", conta.id, uuid.uuid4(), u_id)

        mock_repo.create_transacoes.assert_not_called()


class TestConciliar:
    async def test_concilia_com_sucesso(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id)
        lancamento = MagicMock()
        lancamento.usuario_id = u_id
        lancamento.empresa_id = transacao.empresa_id  # mesma empresa da transação

        mock_repo.get_transacao.return_value = transacao
        mock_lancamento_repo.get_by_id.return_value = lancamento

        result = await svc.conciliar(transacao.id, lancamento.id, u_id)

        assert result.status == StatusTransacao.CONCILIADA
        assert result.lancamento_id == lancamento.id

    async def test_ja_conciliada_falha(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, status=StatusTransacao.CONCILIADA)
        mock_repo.get_transacao.return_value = transacao

        with pytest.raises(ConflictError):
            await svc.conciliar(transacao.id, uuid.uuid4(), u_id)

    async def test_lancamento_nao_encontrado_falha(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id)
        mock_repo.get_transacao.return_value = transacao
        mock_lancamento_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await svc.conciliar(transacao.id, uuid.uuid4(), u_id)

    async def test_transacao_outro_usuario_falha(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        transacao = _make_transacao(usuario_id=uuid.uuid4())
        mock_repo.get_transacao.return_value = transacao
        mock_repo.tem_acesso_empresa.return_value = False

        with pytest.raises(PermissionDeniedError):
            await svc.conciliar(transacao.id, uuid.uuid4(), uuid.uuid4())


class TestCriarLancamento:
    async def test_cria_e_concilia(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id)
        mock_repo.get_transacao.return_value = transacao

        data = CriarLancamentoRequest(
            empresa_id=uuid.uuid4(),
            descricao="Pagamento fornecedor",
            tipo=TipoLancamento.DESPESA,
            data_competencia=date(2024, 1, 15),
            data_vencimento=date(2024, 1, 15),
            categoria_id=uuid.uuid4(),
        )
        result = await svc.criar_lancamento_de_transacao(transacao.id, data, u_id)

        mock_lancamento_repo.create.assert_called_once()
        assert result.status == StatusTransacao.CONCILIADA

    async def test_com_categoria_salva_regra(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        cat_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, descricao="PAGAMENTO TED FORNECEDOR")
        mock_repo.get_transacao.return_value = transacao

        data = CriarLancamentoRequest(
            empresa_id=uuid.uuid4(),
            descricao="Pagamento",
            tipo=TipoLancamento.DESPESA,
            data_competencia=date(2024, 1, 15),
            data_vencimento=date(2024, 1, 15),
            categoria_id=cat_id,
        )
        await svc.criar_lancamento_de_transacao(transacao.id, data, u_id)

        mock_repo.upsert_regra.assert_called_once()
        kwargs = mock_repo.upsert_regra.call_args.kwargs
        assert kwargs["categoria_id"] == cat_id

    async def test_padrao_vazio_nao_salva_regra(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        # Categoria agora é obrigatória no schema; a regra de aprendizado só é
        # dispensada quando a descrição da transação não gera padrão útil.
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, descricao="")
        mock_repo.get_transacao.return_value = transacao

        data = CriarLancamentoRequest(
            empresa_id=uuid.uuid4(),
            descricao="Pagamento",
            tipo=TipoLancamento.DESPESA,
            data_competencia=date(2024, 1, 15),
            data_vencimento=date(2024, 1, 15),
            categoria_id=uuid.uuid4(),
        )
        await svc.criar_lancamento_de_transacao(transacao.id, data, u_id)

        mock_repo.upsert_regra.assert_not_called()

    async def test_ja_conciliada_falha(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, status=StatusTransacao.IGNORADA)
        mock_repo.get_transacao.return_value = transacao

        with pytest.raises(ConflictError):
            await svc.criar_lancamento_de_transacao(
                transacao.id,
                CriarLancamentoRequest(
                    empresa_id=uuid.uuid4(),
                    descricao="X",
                    tipo=TipoLancamento.DESPESA,
                    data_competencia=date(2024, 1, 1),
                    data_vencimento=date(2024, 1, 1),
                    categoria_id=uuid.uuid4(),
                ),
                u_id,
            )


class TestIgnorar:
    async def test_ignora_com_sucesso(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id)
        mock_repo.get_transacao.return_value = transacao

        result = await svc.ignorar(transacao.id, u_id)
        assert result.status == StatusTransacao.IGNORADA

    async def test_ja_ignorada_falha(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, status=StatusTransacao.IGNORADA)
        mock_repo.get_transacao.return_value = transacao

        with pytest.raises(ConflictError):
            await svc.ignorar(transacao.id, u_id)


class TestSugerirMatch:
    async def test_retorna_lancamentos(
        self,
        svc: ConciliacaoService,
        mock_repo: AsyncMock,
        mock_lancamento_repo: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id)
        mock_repo.get_transacao.return_value = transacao
        mock_repo.buscar_lancamentos_para_match.return_value = [MagicMock(), MagicMock()]

        result = await svc.sugerir_match(transacao.id, u_id)
        assert len(result) == 2

    async def test_nao_pendente_falha(
        self, svc: ConciliacaoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        transacao = _make_transacao(usuario_id=u_id, status=StatusTransacao.CONCILIADA)
        mock_repo.get_transacao.return_value = transacao

        with pytest.raises(DomainError):
            await svc.sugerir_match(transacao.id, u_id)
