from decimal import Decimal

import pytest

from app.core.exceptions import DomainError
from app.modules.lancamento.importacao import (
    ler_planilha,
    normalizar_linhas,
    validar_mapeamento,
)


def test_ler_csv_e_normalizar_linhas() -> None:
    conteudo = (
        b"Descricao,Valor,Competencia,Vencimento,Observacoes\n"
        b"Aluguel,1500,01/05/2026,10/05/2026,Pago no banco\n"
    )

    arquivo = ler_planilha("contas.csv", conteudo)
    mapeamento = validar_mapeamento(
        {
            "descricao": "Descricao",
            "valor": "Valor",
            "data_competencia": "Competencia",
            "data_vencimento": "Vencimento",
            "observacoes": "Observacoes",
        }
    )
    itens = normalizar_linhas(arquivo, mapeamento)

    assert arquivo.colunas == ["Descricao", "Valor", "Competencia", "Vencimento", "Observacoes"]
    assert len(itens) == 1
    assert itens[0]["valida"] is True
    assert items_payload(itens, 0, "descricao") == "Aluguel"
    assert items_payload(itens, 0, "valor") == Decimal("1500")


def test_mapeamento_obrigatorio_falta() -> None:
    with pytest.raises(DomainError, match="Campos obrigatórios"):
        validar_mapeamento({"descricao": "Descricao"})


def test_uuid_invalido_vira_erro_de_preview() -> None:
    conteudo = (
        b"Descricao,Valor,Competencia,Vencimento,Categoria\n"
        b"Internet,250,2026-05-01,2026-05-10,financeiro\n"
    )
    arquivo = ler_planilha("contas.csv", conteudo)
    mapeamento = validar_mapeamento(
        {
            "descricao": "Descricao",
            "valor": "Valor",
            "data_competencia": "Competencia",
            "data_vencimento": "Vencimento",
            "categoria_id": "Categoria",
        }
    )

    itens = normalizar_linhas(arquivo, mapeamento)

    assert itens[0]["valida"] is False
    assert "categoria_id deve ser informado como UUID válido." in itens[0]["erros"]


def items_payload(itens: list[dict[str, object]], indice: int, campo: str) -> object:
    payload = itens[indice]["payload"]
    assert isinstance(payload, dict)
    return payload[campo]
