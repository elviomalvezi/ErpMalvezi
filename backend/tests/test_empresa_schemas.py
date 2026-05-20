import pytest
from pydantic import ValidationError

from app.modules.empresa.models import RegimeTributario, TipoPessoa
from app.modules.empresa.schemas import EmpresaCreate

CNPJ_VALIDO = "11222333000181"
CPF_VALIDO = "52998224725"


class TestEmpresaCreatePJ:
    def test_pj_valido(self) -> None:
        data = EmpresaCreate(
            tipo=TipoPessoa.PJ,
            documento=CNPJ_VALIDO,
            nome_principal="Empresa Teste Ltda",
            regime_tributario=RegimeTributario.SIMPLES,
        )
        assert data.tipo == TipoPessoa.PJ

    def test_pj_sem_regime_tributario_falha(self) -> None:
        with pytest.raises(ValidationError, match="Regime tributário"):
            EmpresaCreate(
                tipo=TipoPessoa.PJ,
                documento=CNPJ_VALIDO,
                nome_principal="Empresa Teste Ltda",
            )

    def test_pj_com_inscricao_municipal(self) -> None:
        data = EmpresaCreate(
            tipo=TipoPessoa.PJ,
            documento=CNPJ_VALIDO,
            nome_principal="Empresa Teste Ltda",
            regime_tributario=RegimeTributario.SIMPLES,
            documento_complementar_2="12345",
        )
        assert data.documento_complementar_2 == "12345"


class TestEmpresaCreatePF:
    def test_pf_valido(self) -> None:
        data = EmpresaCreate(
            tipo=TipoPessoa.PF,
            documento=CPF_VALIDO,
            nome_principal="João da Silva",
        )
        assert data.tipo == TipoPessoa.PF

    def test_pf_com_inscricao_municipal_falha(self) -> None:
        with pytest.raises(ValidationError, match="Inscrição Municipal"):
            EmpresaCreate(
                tipo=TipoPessoa.PF,
                documento=CPF_VALIDO,
                nome_principal="João da Silva",
                documento_complementar_2="12345",
            )

    def test_pf_nao_precisa_regime_tributario(self) -> None:
        data = EmpresaCreate(
            tipo=TipoPessoa.PF,
            documento=CPF_VALIDO,
            nome_principal="João da Silva",
        )
        assert data.regime_tributario is None


class TestSeparadores:
    def test_separadores_iguais_falha(self) -> None:
        with pytest.raises(ValidationError, match="Separador decimal"):
            EmpresaCreate(
                tipo=TipoPessoa.PF,
                documento=CPF_VALIDO,
                nome_principal="João da Silva",
                separador_decimal=",",
                separador_milhares=",",
            )

    def test_cor_invalida_falha(self) -> None:
        with pytest.raises(ValidationError):
            EmpresaCreate(
                tipo=TipoPessoa.PF,
                documento=CPF_VALIDO,
                nome_principal="João da Silva",
                cor_primaria="vermelho",
            )

    def test_cor_hex_valida(self) -> None:
        data = EmpresaCreate(
            tipo=TipoPessoa.PF,
            documento=CPF_VALIDO,
            nome_principal="João da Silva",
            cor_primaria="#1A2B3C",
        )
        assert data.cor_primaria == "#1A2B3C"
