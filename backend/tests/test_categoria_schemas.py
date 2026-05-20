import uuid

import pytest
from pydantic import ValidationError

from app.modules.categoria.models import EscopoCategoria, TipoCategoria
from app.modules.categoria.schemas import CategoriaCreate, CategoriaUpdate


class TestCategoriaCreate:
    def test_global_sem_empresa_valido(self) -> None:
        data = CategoriaCreate(
            nome="Receitas",
            tipo=TipoCategoria.RECEITA,
            escopo=EscopoCategoria.GLOBAL,
        )
        assert data.empresa_id is None

    def test_especifico_com_empresa_valido(self) -> None:
        empresa_id = uuid.uuid4()
        data = CategoriaCreate(
            nome="Receitas Locais",
            tipo=TipoCategoria.RECEITA,
            escopo=EscopoCategoria.ESPECIFICO,
            empresa_id=empresa_id,
        )
        assert data.empresa_id == empresa_id

    def test_especifico_sem_empresa_falha(self) -> None:
        with pytest.raises(ValidationError, match="empresa_id é obrigatório"):
            CategoriaCreate(
                nome="Receitas Locais",
                tipo=TipoCategoria.RECEITA,
                escopo=EscopoCategoria.ESPECIFICO,
            )

    def test_global_com_empresa_falha(self) -> None:
        with pytest.raises(ValidationError, match="empresa_id deve ser nulo"):
            CategoriaCreate(
                nome="Receitas",
                tipo=TipoCategoria.RECEITA,
                escopo=EscopoCategoria.GLOBAL,
                empresa_id=uuid.uuid4(),
            )

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            CategoriaCreate(nome="A", tipo=TipoCategoria.RECEITA)

    def test_escopo_default_global(self) -> None:
        data = CategoriaCreate(nome="Despesas", tipo=TipoCategoria.DESPESA)
        assert data.escopo == EscopoCategoria.GLOBAL


class TestCategoriaUpdate:
    def test_todos_opcionais(self) -> None:
        data = CategoriaUpdate()
        assert data.nome is None
        assert data.codigo is None

    def test_nome_muito_curto_falha(self) -> None:
        with pytest.raises(ValidationError):
            CategoriaUpdate(nome="X")
