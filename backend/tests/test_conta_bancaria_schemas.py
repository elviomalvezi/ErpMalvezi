import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.conta_bancaria.models import BandeiraCartao, TipoConta
from app.modules.conta_bancaria.schemas import ContaBancariaCreate, ContaBancariaUpdate


class TestContaBancariaCreate:
    def test_corrente_valido(self) -> None:
        data = ContaBancariaCreate(
            empresa_id=uuid.uuid4(),
            nome="Conta Corrente BB",
            tipo=TipoConta.CORRENTE,
            banco="Banco do Brasil",
            agencia="1234",
            numero_conta="56789",
        )
        assert data.saldo_inicial == Decimal("0")
        assert data.bandeira is None

    def test_caixinha_sem_dados_bancarios(self) -> None:
        data = ContaBancariaCreate(
            empresa_id=uuid.uuid4(),
            nome="Caixinha",
            tipo=TipoConta.CAIXINHA,
        )
        assert data.agencia is None

    def test_cartao_completo_valido(self) -> None:
        data = ContaBancariaCreate(
            empresa_id=uuid.uuid4(),
            nome="Nubank",
            tipo=TipoConta.CARTAO_CREDITO,
            bandeira=BandeiraCartao.MASTERCARD,
            limite=Decimal("5000"),
            dia_vencimento=10,
            dia_fechamento=3,
        )
        assert data.limite == Decimal("5000")
        assert data.dia_vencimento == 10

    def test_cartao_sem_limite_falha(self) -> None:
        with pytest.raises(ValidationError, match="limite é obrigatório"):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Nubank",
                tipo=TipoConta.CARTAO_CREDITO,
                dia_vencimento=10,
                dia_fechamento=3,
            )

    def test_cartao_sem_dia_vencimento_falha(self) -> None:
        with pytest.raises(ValidationError, match="dia_vencimento é obrigatório"):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Nubank",
                tipo=TipoConta.CARTAO_CREDITO,
                limite=Decimal("5000"),
                dia_fechamento=3,
            )

    def test_cartao_sem_dia_fechamento_falha(self) -> None:
        with pytest.raises(ValidationError, match="dia_fechamento é obrigatório"):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Nubank",
                tipo=TipoConta.CARTAO_CREDITO,
                limite=Decimal("5000"),
                dia_vencimento=10,
            )

    def test_corrente_com_bandeira_falha(self) -> None:
        with pytest.raises(ValidationError, match="bandeira é exclusivo"):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Corrente",
                tipo=TipoConta.CORRENTE,
                bandeira=BandeiraCartao.VISA,
            )

    def test_corrente_com_limite_falha(self) -> None:
        with pytest.raises(ValidationError, match="limite é exclusivo"):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Corrente",
                tipo=TipoConta.CORRENTE,
                limite=Decimal("1000"),
            )

    def test_dia_vencimento_fora_do_range_falha(self) -> None:
        with pytest.raises(ValidationError):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="Nubank",
                tipo=TipoConta.CARTAO_CREDITO,
                limite=Decimal("5000"),
                dia_vencimento=32,
                dia_fechamento=3,
            )

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            ContaBancariaCreate(
                empresa_id=uuid.uuid4(),
                nome="X",
                tipo=TipoConta.CORRENTE,
            )


class TestContaBancariaUpdate:
    def test_todos_opcionais(self) -> None:
        data = ContaBancariaUpdate()
        assert data.nome is None
        assert data.limite is None

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            ContaBancariaUpdate(nome="X")
