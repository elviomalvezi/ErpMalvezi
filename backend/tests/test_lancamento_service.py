import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.conta_bancaria.models import ContaBancaria, TipoConta
from app.modules.fatura.models import Fatura
from app.modules.lancamento.models import (
    FrequenciaRecorrencia,
    Lancamento,
    StatusLancamento,
    TipoLancamento,
)
from app.modules.lancamento.schemas import (
    LancamentoBaixaCreate,
    LancamentoCreate,
    LancamentoParceladoCreate,
    LancamentoRecorrenteCreate,
    LancamentoUpdate,
)
from app.modules.lancamento.service import LancamentoService, _add_meses, _dividir_valor

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_conta_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_fatura_svc() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(
    mock_repo: AsyncMock,
    mock_conta_repo: AsyncMock,
    mock_fatura_svc: AsyncMock,
) -> LancamentoService:
    return LancamentoService(mock_repo, mock_conta_repo, mock_fatura_svc)


def _make_lancamento(
    status: StatusLancamento = StatusLancamento.PENDENTE,
    usuario_id: uuid.UUID | None = None,
    fatura_id: uuid.UUID | None = None,
    valor: Decimal = Decimal("100"),
    valor_pago: Decimal = Decimal("0"),
) -> MagicMock:
    lct = MagicMock(spec=Lancamento)
    lct.id = uuid.uuid4()
    lct.usuario_id = usuario_id or uuid.uuid4()
    lct.empresa_id = uuid.uuid4()
    lct.tipo = TipoLancamento.DESPESA
    lct.descricao = "Teste"
    lct.valor = valor
    lct.valor_pago = valor_pago
    lct.data_competencia = date(2024, 1, 1)
    lct.data_vencimento = date(2024, 1, 31)
    lct.data_pagamento = None
    lct.status = status
    lct.categoria_id = None
    lct.contato_id = None
    lct.conta_bancaria_id = None
    lct.fatura_id = fatura_id
    lct.numero_parcela = None
    lct.total_parcelas = None
    lct.grupo_parcelas_id = None
    lct.recorrencia_id = None
    lct.observacoes = None
    lct.ativo = True
    return lct


def _make_conta(
    tipo: TipoConta = TipoConta.CORRENTE,
    usuario_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock(spec=ContaBancaria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.tipo = tipo
    c.dia_fechamento = 3
    c.dia_vencimento = 10
    c.empresa_id = uuid.uuid4()
    return c


def _make_fatura(usuario_id: uuid.UUID | None = None) -> MagicMock:
    f = MagicMock(spec=Fatura)
    f.id = uuid.uuid4()
    f.usuario_id = usuario_id or uuid.uuid4()
    return f


def _make_create(
    conta_bancaria_id: uuid.UUID | None = None,
    tipo: TipoLancamento = TipoLancamento.DESPESA,
) -> LancamentoCreate:
    return LancamentoCreate(
        empresa_id=uuid.uuid4(),
        tipo=tipo,
        descricao="Aluguel Janeiro",
        valor=Decimal("1500"),
        data_competencia=date(2024, 1, 1),
        data_vencimento=date(2024, 1, 10),
        conta_bancaria_id=conta_bancaria_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Funções puras
# ──────────────────────────────────────────────────────────────────────────────

class TestAddMeses:
    def test_simples(self) -> None:
        assert _add_meses(date(2024, 1, 15), 1) == date(2024, 2, 15)

    def test_virada_ano(self) -> None:
        assert _add_meses(date(2024, 12, 1), 1) == date(2025, 1, 1)

    def test_clamp_fevereiro(self) -> None:
        assert _add_meses(date(2024, 1, 31), 1) == date(2024, 2, 29)  # bissexto

    def test_clamp_fevereiro_nao_bissexto(self) -> None:
        assert _add_meses(date(2023, 1, 31), 1) == date(2023, 2, 28)

    def test_clamp_marco(self) -> None:
        assert _add_meses(date(2024, 1, 31), 2) == date(2024, 3, 31)


class TestDividirValor:
    def test_divisao_exata(self) -> None:
        valores = _dividir_valor(Decimal("300"), 3)
        assert valores == [Decimal("100"), Decimal("100"), Decimal("100")]

    def test_com_resto(self) -> None:
        valores = _dividir_valor(Decimal("100"), 3)
        assert len(valores) == 3
        assert sum(valores) == Decimal("100")
        assert valores[0] == Decimal("33.33")
        assert valores[1] == Decimal("33.33")
        assert valores[2] == Decimal("33.34")  # resto vai para a última

    def test_valor_grande(self) -> None:
        valores = _dividir_valor(Decimal("1000.01"), 2)
        assert sum(valores) == Decimal("1000.01")


# ──────────────────────────────────────────────────────────────────────────────
# CriarSimples
# ──────────────────────────────────────────────────────────────────────────────

class TestCriarSimples:
    async def test_cria_lancamento(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None  # sem conta → fatura=None
        mock_repo.create.side_effect = lambda x: x

        lct = await svc.criar_simples(_make_create(), u_id)
        assert lct.usuario_id == u_id
        assert lct.fatura_id is None
        assert lct.status == StatusLancamento.PENDENTE

    async def test_cria_com_cartao_vincula_fatura(
        self,
        svc: LancamentoService,
        mock_repo: AsyncMock,
        mock_conta_repo: AsyncMock,
        mock_fatura_svc: AsyncMock,
    ) -> None:
        u_id = uuid.uuid4()
        cartao = _make_conta(tipo=TipoConta.CARTAO_CREDITO, usuario_id=u_id)
        fatura = _make_fatura(usuario_id=u_id)
        mock_conta_repo.get_by_id.return_value = cartao
        mock_fatura_svc.obter_ou_criar_fatura_aberta.return_value = fatura
        mock_repo.create.side_effect = lambda x: x

        lct = await svc.criar_simples(_make_create(conta_bancaria_id=cartao.id), u_id)
        assert lct.fatura_id == fatura.id
        mock_fatura_svc.delta_valor_total.assert_called_once_with(fatura.id, Decimal("1500"))

    async def test_empresa_sem_vinculo_falha(
        self,
        mock_repo: AsyncMock,
        mock_conta_repo: AsyncMock,
        mock_fatura_svc: AsyncMock,
    ) -> None:
        # Regra atual: o acesso é validado pelo vínculo usuário × empresa,
        # não pela propriedade da conta.
        mock_empresa_repo = AsyncMock()
        mock_empresa_repo.get_vinculo.return_value = None
        svc = LancamentoService(
            mock_repo, mock_conta_repo, mock_fatura_svc, empresa_repo=mock_empresa_repo
        )

        with pytest.raises(PermissionDeniedError):
            await svc.criar_simples(_make_create(), uuid.uuid4())

    async def test_conta_nao_encontrada_falha(
        self,
        svc: LancamentoService,
        mock_conta_repo: AsyncMock,
    ) -> None:
        mock_conta_repo.get_by_id.return_value = None
        cid = uuid.uuid4()

        with pytest.raises(NotFoundError):
            await svc.criar_simples(_make_create(conta_bancaria_id=cid), uuid.uuid4())


# ──────────────────────────────────────────────────────────────────────────────
# CriarParcelado
# ──────────────────────────────────────────────────────────────────────────────

class TestCriarParcelado:
    async def test_cria_tres_parcelas(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None
        mock_repo.create_many.return_value = None

        data = LancamentoParceladoCreate(
            empresa_id=uuid.uuid4(),
            tipo=TipoLancamento.DESPESA,
            descricao="Compra Parcelada",
            valor_total=Decimal("300"),
            parcelas=3,
            data_primeira_competencia=date(2024, 1, 1),
            data_primeiro_vencimento=date(2024, 1, 10),
        )
        lancamentos = await svc.criar_parcelado(data, u_id)

        assert len(lancamentos) == 3
        assert lancamentos[0].numero_parcela == 1
        assert lancamentos[2].numero_parcela == 3
        assert lancamentos[0].total_parcelas == 3
        # Todas têm o mesmo grupo
        grupo_id = lancamentos[0].grupo_parcelas_id
        assert all(lct.grupo_parcelas_id == grupo_id for lct in lancamentos)
        # Total correto
        assert sum(lct.valor for lct in lancamentos) == Decimal("300")

    async def test_datas_avancam_um_mes(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None
        mock_repo.create_many.return_value = None

        data = LancamentoParceladoCreate(
            empresa_id=uuid.uuid4(),
            tipo=TipoLancamento.DESPESA,
            descricao="Parcelas",
            valor_total=Decimal("200"),
            parcelas=2,
            data_primeira_competencia=date(2024, 1, 1),
            data_primeiro_vencimento=date(2024, 1, 15),
        )
        lancamentos = await svc.criar_parcelado(data, u_id)

        assert lancamentos[0].data_vencimento == date(2024, 1, 15)
        assert lancamentos[1].data_vencimento == date(2024, 2, 15)

    async def test_descricao_com_numero_parcela(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None
        mock_repo.create_many.return_value = None

        data = LancamentoParceladoCreate(
            empresa_id=uuid.uuid4(),
            tipo=TipoLancamento.DESPESA,
            descricao="TV",
            valor_total=Decimal("1000"),
            parcelas=2,
            data_primeira_competencia=date(2024, 1, 1),
            data_primeiro_vencimento=date(2024, 1, 10),
        )
        lancamentos = await svc.criar_parcelado(data, u_id)
        assert "1/2" in lancamentos[0].descricao
        assert "2/2" in lancamentos[1].descricao


# ──────────────────────────────────────────────────────────────────────────────
# CriarRecorrente
# ──────────────────────────────────────────────────────────────────────────────

class TestCriarRecorrente:
    async def test_cria_mensal(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None
        mock_repo.create_many.return_value = None

        data = LancamentoRecorrenteCreate(
            empresa_id=uuid.uuid4(),
            tipo=TipoLancamento.DESPESA,
            descricao="Aluguel",
            valor=Decimal("2000"),
            data_primeira_competencia=date(2024, 1, 1),
            data_primeiro_vencimento=date(2024, 1, 5),
            frequencia=FrequenciaRecorrencia.MENSAL,
            quantidade=12,
        )
        lancamentos = await svc.criar_recorrente(data, u_id)

        assert len(lancamentos) == 12
        assert all(lct.valor == Decimal("2000") for lct in lancamentos)
        assert all(lct.recorrencia_id == lancamentos[0].recorrencia_id for lct in lancamentos)
        assert lancamentos[0].data_vencimento == date(2024, 1, 5)
        assert lancamentos[11].data_vencimento == date(2024, 12, 5)

    async def test_cria_semanal(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        mock_conta_repo.get_by_id.return_value = None
        mock_repo.create_many.return_value = None

        data = LancamentoRecorrenteCreate(
            empresa_id=uuid.uuid4(),
            tipo=TipoLancamento.DESPESA,
            descricao="Faxina",
            valor=Decimal("150"),
            data_primeira_competencia=date(2024, 1, 1),
            data_primeiro_vencimento=date(2024, 1, 1),
            frequencia=FrequenciaRecorrencia.SEMANAL,
            quantidade=4,
        )
        lancamentos = await svc.criar_recorrente(data, u_id)

        assert lancamentos[0].data_vencimento == date(2024, 1, 1)
        assert lancamentos[1].data_vencimento == date(2024, 1, 8)
        assert lancamentos[3].data_vencimento == date(2024, 1, 22)


# ──────────────────────────────────────────────────────────────────────────────
# Baixa
# ──────────────────────────────────────────────────────────────────────────────

class TestRegistrarBaixa:
    async def test_baixa_total(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_conta_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(usuario_id=u_id, valor=Decimal("100"))
        mock_repo.get_by_id.return_value = lct

        result = await svc.registrar_baixa(
            lct.id,
            LancamentoBaixaCreate(
                valor_pago=Decimal("100"),
                data_pagamento=date(2024, 1, 10),
                conta_bancaria_id=uuid.uuid4(),
                categoria_id=uuid.uuid4(),
            ),
            u_id,
        )
        assert result.status == StatusLancamento.PAGO
        assert result.valor_pago == Decimal("100")

    async def test_baixa_parcial_mantem_pendente(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(usuario_id=u_id, valor=Decimal("100"), valor_pago=Decimal("0"))
        mock_repo.get_by_id.return_value = lct

        result = await svc.registrar_baixa(
            lct.id,
            LancamentoBaixaCreate(
                valor_pago=Decimal("40"),
                data_pagamento=date(2024, 1, 5),
                conta_bancaria_id=uuid.uuid4(),
                categoria_id=uuid.uuid4(),
            ),
            u_id,
        )
        assert result.status == StatusLancamento.PENDENTE
        assert result.valor_pago == Decimal("40")

    async def test_baixa_acima_do_valor_marca_pago(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        # Regra atual: é permitido baixar acima do previsto (pagamento maior que
        # o valor do lançamento); o total acumula e o status vira PAGO.
        u_id = uuid.uuid4()
        lct = _make_lancamento(usuario_id=u_id, valor=Decimal("100"), valor_pago=Decimal("60"))
        mock_repo.get_by_id.return_value = lct

        result = await svc.registrar_baixa(
            lct.id,
            LancamentoBaixaCreate(
                valor_pago=Decimal("50"),
                data_pagamento=date(2024, 1, 10),
                conta_bancaria_id=uuid.uuid4(),
                categoria_id=uuid.uuid4(),
            ),
            u_id,
        )
        assert result.valor_pago == Decimal("110")
        assert result.status == StatusLancamento.PAGO

    async def test_ja_pago_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.PAGO, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(ConflictError, match="já está totalmente pago"):
            await svc.registrar_baixa(
                lct.id,
                LancamentoBaixaCreate(
                    valor_pago=Decimal("100"),
                    data_pagamento=date(2024, 1, 10),
                    conta_bancaria_id=uuid.uuid4(),
                    categoria_id=uuid.uuid4(),
                ),
                u_id,
            )

    async def test_vinculado_a_fatura_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(usuario_id=u_id, fatura_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(DomainError, match="fatura de cartão"):
            await svc.registrar_baixa(
                lct.id,
                LancamentoBaixaCreate(
                    valor_pago=Decimal("100"),
                    data_pagamento=date(2024, 1, 10),
                    conta_bancaria_id=uuid.uuid4(),
                    categoria_id=uuid.uuid4(),
                ),
                u_id,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Cancelar
# ──────────────────────────────────────────────────────────────────────────────

class TestCancelar:
    async def test_cancela_pendente(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.PENDENTE, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        result = await svc.cancelar(lct.id, u_id)
        assert result.status == StatusLancamento.CANCELADO
        assert result.ativo is False

    async def test_cancela_com_fatura_atualiza_total(
        self, svc: LancamentoService, mock_repo: AsyncMock, mock_fatura_svc: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        fatura_id = uuid.uuid4()
        lct = _make_lancamento(
            status=StatusLancamento.PENDENTE,
            usuario_id=u_id,
            fatura_id=fatura_id,
            valor=Decimal("500"),
        )
        mock_repo.get_by_id.return_value = lct

        await svc.cancelar(lct.id, u_id)
        mock_fatura_svc.delta_valor_total.assert_called_once_with(fatura_id, Decimal("-500"))

    async def test_cancelar_pago_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.PAGO, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(DomainError, match="já pago"):
            await svc.cancelar(lct.id, u_id)

    async def test_cancelar_ja_cancelado_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.CANCELADO, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(ConflictError, match="já está cancelado"):
            await svc.cancelar(lct.id, u_id)


# ──────────────────────────────────────────────────────────────────────────────
# Atualizar
# ──────────────────────────────────────────────────────────────────────────────

class TestAtualizar:
    async def test_atualiza_descricao(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        await svc.atualizar(lct.id, LancamentoUpdate(descricao="Nova Descricao"), u_id)
        assert lct.descricao == "Nova Descricao"

    async def test_editar_cancelado_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.CANCELADO, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(DomainError, match="cancelado"):
            await svc.atualizar(lct.id, LancamentoUpdate(descricao="X novo"), u_id)

    async def test_editar_pago_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        lct = _make_lancamento(status=StatusLancamento.PAGO, usuario_id=u_id)
        mock_repo.get_by_id.return_value = lct

        with pytest.raises(DomainError, match="já pago"):
            await svc.atualizar(lct.id, LancamentoUpdate(descricao="X novo"), u_id)


# ──────────────────────────────────────────────────────────────────────────────
# Obter
# ──────────────────────────────────────────────────────────────────────────────

class TestObter:
    async def test_nao_encontrado(self, svc: LancamentoService, mock_repo: AsyncMock) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.obter(uuid.uuid4(), uuid.uuid4())

    async def test_outro_usuario_falha(
        self, svc: LancamentoService, mock_repo: AsyncMock
    ) -> None:
        lct = _make_lancamento(usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = lct
        mock_repo.tem_acesso.return_value = False
        with pytest.raises(PermissionDeniedError):
            await svc.obter(lct.id, uuid.uuid4())
