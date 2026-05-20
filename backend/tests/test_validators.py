
from app.modules.empresa.validators import (
    formatar_documento,
    normalizar_documento,
    validar_cnpj,
    validar_cpf,
)


class TestValidarCNPJ:
    def test_cnpj_valido(self) -> None:
        assert validar_cnpj("11.222.333/0001-81") is True

    def test_cnpj_valido_somente_digitos(self) -> None:
        assert validar_cnpj("11222333000181") is True

    def test_cnpj_invalido(self) -> None:
        assert validar_cnpj("11.222.333/0001-00") is False

    def test_cnpj_sequencia_repetida(self) -> None:
        assert validar_cnpj("11111111111111") is False

    def test_cnpj_comprimento_errado(self) -> None:
        assert validar_cnpj("1234567890") is False

    def test_cnpj_zerado(self) -> None:
        assert validar_cnpj("00000000000000") is False


class TestValidarCPF:
    def test_cpf_valido(self) -> None:
        assert validar_cpf("529.982.247-25") is True

    def test_cpf_valido_somente_digitos(self) -> None:
        assert validar_cpf("52998224725") is True

    def test_cpf_invalido(self) -> None:
        assert validar_cpf("529.982.247-00") is False

    def test_cpf_sequencia_repetida(self) -> None:
        assert validar_cpf("11111111111") is False

    def test_cpf_comprimento_errado(self) -> None:
        assert validar_cpf("1234567") is False


class TestFormatarDocumento:
    def test_formatar_cnpj(self) -> None:
        assert formatar_documento("11222333000181", "PJ") == "11.222.333/0001-81"

    def test_formatar_cpf(self) -> None:
        assert formatar_documento("52998224725", "PF") == "529.982.247-25"


class TestNormalizarDocumento:
    def test_remove_mascara(self) -> None:
        assert normalizar_documento("11.222.333/0001-81") == "11222333000181"

    def test_ja_normalizado(self) -> None:
        assert normalizar_documento("11222333000181") == "11222333000181"
