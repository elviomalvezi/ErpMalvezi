import uuid

import pytest
from pydantic import ValidationError

from app.modules.contato.models import EscopoContato, TipoContato
from app.modules.contato.schemas import ContatoCreate, ContatoUpdate

# CPF e CNPJ válidos para testes (algoritmo correto)
CPF_VALIDO = "52998224725"   # dígitos
CNPJ_VALIDO = "11222333000181"  # dígitos


class TestContatoCreate:
    def test_pf_cpf_valido(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PF,
            documento=CPF_VALIDO,
            nome_principal="João Silva",
        )
        assert data.documento == CPF_VALIDO
        assert data.escopo == EscopoContato.GLOBAL

    def test_pj_cnpj_valido(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PJ,
            documento=CNPJ_VALIDO,
            nome_principal="Empresa Exemplo Ltda",
        )
        assert data.documento == CNPJ_VALIDO
        assert data.eh_cliente is True
        assert data.eh_fornecedor is False

    def test_documento_normalizado(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PF,
            documento="529.982.247-25",
            nome_principal="João Silva",
        )
        assert data.documento == CPF_VALIDO

    def test_cnpj_formatado_normalizado(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PJ,
            documento="11.222.333/0001-81",
            nome_principal="Empresa",
        )
        assert data.documento == CNPJ_VALIDO

    def test_cpf_invalido_falha(self) -> None:
        with pytest.raises(ValidationError, match="CPF inválido"):
            ContatoCreate(
                tipo=TipoContato.PF,
                documento="11111111111",
                nome_principal="Teste",
            )

    def test_cnpj_invalido_falha(self) -> None:
        with pytest.raises(ValidationError, match="CNPJ inválido"):
            ContatoCreate(
                tipo=TipoContato.PJ,
                documento="00000000000000",
                nome_principal="Empresa",
            )

    def test_escopo_especifico_sem_empresa_falha(self) -> None:
        with pytest.raises(ValidationError, match="empresa_id é obrigatório"):
            ContatoCreate(
                tipo=TipoContato.PF,
                documento=CPF_VALIDO,
                nome_principal="João",
                escopo=EscopoContato.ESPECIFICO,
            )

    def test_escopo_global_com_empresa_falha(self) -> None:
        with pytest.raises(ValidationError, match="empresa_id deve ser nulo"):
            ContatoCreate(
                tipo=TipoContato.PF,
                documento=CPF_VALIDO,
                nome_principal="João",
                escopo=EscopoContato.GLOBAL,
                empresa_id=uuid.uuid4(),
            )

    def test_nem_cliente_nem_fornecedor_falha(self) -> None:
        with pytest.raises(ValidationError, match="cliente, fornecedor ou ambos"):
            ContatoCreate(
                tipo=TipoContato.PF,
                documento=CPF_VALIDO,
                nome_principal="João",
                eh_cliente=False,
                eh_fornecedor=False,
            )

    def test_cliente_e_fornecedor_simultaneo(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PF,
            documento=CPF_VALIDO,
            nome_principal="João",
            eh_cliente=True,
            eh_fornecedor=True,
        )
        assert data.eh_cliente is True
        assert data.eh_fornecedor is True

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            ContatoCreate(
                tipo=TipoContato.PF,
                documento=CPF_VALIDO,
                nome_principal="J",
            )

    def test_escopo_especifico_com_empresa_valido(self) -> None:
        data = ContatoCreate(
            tipo=TipoContato.PJ,
            documento=CNPJ_VALIDO,
            nome_principal="Empresa",
            escopo=EscopoContato.ESPECIFICO,
            empresa_id=uuid.uuid4(),
        )
        assert data.empresa_id is not None


class TestContatoUpdate:
    def test_todos_opcionais(self) -> None:
        data = ContatoUpdate()
        assert data.nome_principal is None
        assert data.documento is None

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            ContatoUpdate(nome_principal="X")

    def test_documento_normalizado(self) -> None:
        data = ContatoUpdate(documento="529.982.247-25")
        assert data.documento == CPF_VALIDO
