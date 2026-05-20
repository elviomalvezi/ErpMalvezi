from datetime import date
from decimal import Decimal

from app.modules.conciliacao.parser import parse_csv, parse_ofx

_OFX_SAMPLE = b"""
OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<CURDEF>BRL
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20240115
<TRNAMT>-500.00
<FITID>TX001
<MEMO>PAGAMENTO TED FORNECEDOR
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20240116
<TRNAMT>1000.00
<FITID>TX002
<MEMO>RECEBIMENTO CLIENTE ABC
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20240117
<TRNAMT>-250.50
<FITID>TX003
<NAME>TAXA SERVICO
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""


class TestParseOFX:
    def test_extrai_tres_transacoes(self) -> None:
        result = parse_ofx(_OFX_SAMPLE)
        assert len(result) == 3

    def test_transacao_debito(self) -> None:
        result = parse_ofx(_OFX_SAMPLE)
        tx = result[0]
        assert tx["id_externo"] == "TX001"
        assert tx["data"] == date(2024, 1, 15)
        assert tx["valor"] == Decimal("500.00")
        assert tx["tipo"] == "debito"
        assert "FORNECEDOR" in tx["descricao"]

    def test_transacao_credito(self) -> None:
        result = parse_ofx(_OFX_SAMPLE)
        tx = result[1]
        assert tx["id_externo"] == "TX002"
        assert tx["data"] == date(2024, 1, 16)
        assert tx["valor"] == Decimal("1000.00")
        assert tx["tipo"] == "credito"

    def test_valor_sempre_positivo(self) -> None:
        result = parse_ofx(_OFX_SAMPLE)
        for tx in result:
            assert tx["valor"] > 0

    def test_fallback_name_sem_memo(self) -> None:
        result = parse_ofx(_OFX_SAMPLE)
        tx = result[2]
        assert tx["descricao"] == "TAXA SERVICO"
        assert tx["valor"] == Decimal("250.50")

    def test_arquivo_vazio(self) -> None:
        result = parse_ofx(b"OFXHEADER:100\nDATA:OFXSGML\n")
        assert result == []


_CSV_SAMPLE = b"""Data;Descricao;Valor
15/01/2024;PAGAMENTO TED FORNECEDOR;-500,00
16/01/2024;RECEBIMENTO CLIENTE ABC;1.000,00
17/01/2024;TAXA SERVICO;-250,50
"""


class TestParseCSV:
    def test_extrai_tres_transacoes(self) -> None:
        result = parse_csv(_CSV_SAMPLE)
        assert len(result) == 3

    def test_debito_negativo(self) -> None:
        result = parse_csv(_CSV_SAMPLE)
        assert result[0]["tipo"] == "debito"
        assert result[0]["valor"] == Decimal("500.00")
        assert result[0]["data"] == date(2024, 1, 15)

    def test_credito_positivo(self) -> None:
        result = parse_csv(_CSV_SAMPLE)
        assert result[1]["tipo"] == "credito"
        assert result[1]["valor"] == Decimal("1000.00")

    def test_valor_com_ponto_milhar(self) -> None:
        result = parse_csv(_CSV_SAMPLE)
        assert result[1]["valor"] == Decimal("1000.00")

    def test_sem_id_externo(self) -> None:
        result = parse_csv(_CSV_SAMPLE)
        for tx in result:
            assert tx["id_externo"] is None

    def test_linha_vazia_ignorada(self) -> None:
        content = b"Data;Descricao;Valor\n15/01/2024;PAGAMENTO;-100,00\n\n"
        result = parse_csv(content)
        assert len(result) == 1

    def test_linha_invalida_ignorada(self) -> None:
        content = b"Data;Descricao;Valor\nNAO_E_DATA;DESC;-100,00\n15/01/2024;DESC;-200,00\n"
        result = parse_csv(content)
        assert len(result) == 1
        assert result[0]["valor"] == Decimal("200.00")

    def test_sem_cabecalho(self) -> None:
        content = b"15/01/2024;PAGAMENTO;-100,00\n"
        result = parse_csv(content, skip_header=False)
        assert len(result) == 1

    def test_delimitador_virgula(self) -> None:
        content = b"Data,Descricao,Valor\n15/01/2024,PAGAMENTO,-100.50\n"
        result = parse_csv(content, delimiter=",", decimal_sep=".")
        assert len(result) == 1
        assert result[0]["valor"] == Decimal("100.50")
