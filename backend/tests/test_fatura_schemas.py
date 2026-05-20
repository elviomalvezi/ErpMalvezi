import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.fatura.schemas import FaturaCreate, FaturaPagamentoCreate


class TestFaturaCreate:
    def test_competencia_normalizada_para_dia_1(self) -> None:
        data = FaturaCreate(
            conta_bancaria_id=uuid.uuid4(),
            competencia=date(2024, 3, 15),
        )
        assert data.competencia == date(2024, 3, 1)

    def test_competencia_ja_no_dia_1(self) -> None:
        data = FaturaCreate(
            conta_bancaria_id=uuid.uuid4(),
            competencia=date(2024, 6, 1),
        )
        assert data.competencia == date(2024, 6, 1)


class TestFaturaPagamentoCreate:
    def test_valido(self) -> None:
        data = FaturaPagamentoCreate(
            conta_pagamento_id=uuid.uuid4(),
            data_pagamento=date(2024, 2, 10),
            valor_pago=Decimal("1500.00"),
        )
        assert data.valor_pago == Decimal("1500.00")

    def test_valor_zero_falha(self) -> None:
        with pytest.raises(ValidationError):
            FaturaPagamentoCreate(
                conta_pagamento_id=uuid.uuid4(),
                data_pagamento=date(2024, 2, 10),
                valor_pago=Decimal("0"),
            )

    def test_valor_negativo_falha(self) -> None:
        with pytest.raises(ValidationError):
            FaturaPagamentoCreate(
                conta_pagamento_id=uuid.uuid4(),
                data_pagamento=date(2024, 2, 10),
                valor_pago=Decimal("-100"),
            )
