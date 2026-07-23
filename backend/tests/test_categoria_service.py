import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, DomainError, PermissionDeniedError
from app.modules.categoria.models import Categoria, EscopoCategoria, TipoCategoria
from app.modules.categoria.schemas import CategoriaCreate
from app.modules.categoria.service import CategoriaService, _construir_arvore


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> CategoriaService:
    return CategoriaService(mock_repo)


def _make_cat(
    nivel: int = 1,
    ativa: bool = True,
    usuario_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock(spec=Categoria)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.parent_id = parent_id
    c.nivel = nivel
    c.ativa = ativa
    c.tipo = TipoCategoria.RECEITA
    c.escopo = EscopoCategoria.GLOBAL
    c.empresa_id = None
    c.exigir_veiculo = False
    c.exigir_imovel = False
    return c


class TestCriar:
    async def test_nivel_1_sem_parent(self, svc: CategoriaService, mock_repo: AsyncMock) -> None:
        mock_repo.create.side_effect = lambda c: c
        u_id = uuid.uuid4()

        cat = await svc.criar(
            CategoriaCreate(nome="Receitas", tipo=TipoCategoria.RECEITA), u_id
        )
        assert cat.nivel == 1
        assert cat.parent_id is None

    async def test_nivel_2_com_parent(self, svc: CategoriaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        parent = _make_cat(nivel=1, usuario_id=u_id)
        mock_repo.get_by_id.return_value = parent
        mock_repo.create.side_effect = lambda c: c

        cat = await svc.criar(
            CategoriaCreate(
                nome="Subgrupo", tipo=TipoCategoria.RECEITA, parent_id=parent.id
            ),
            u_id,
        )
        assert cat.nivel == 2

    async def test_nivel_4_falha(self, svc: CategoriaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        parent = _make_cat(nivel=3, usuario_id=u_id)
        mock_repo.get_by_id.return_value = parent

        with pytest.raises(DomainError, match="máxima"):
            await svc.criar(
                CategoriaCreate(
                    nome="Quarto nível", tipo=TipoCategoria.RECEITA, parent_id=parent.id
                ),
                u_id,
            )

    async def test_parent_inativo_falha(
        self, svc: CategoriaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        parent = _make_cat(nivel=1, ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = parent

        with pytest.raises(DomainError, match="inativa"):
            await svc.criar(
                CategoriaCreate(
                    nome="Sub", tipo=TipoCategoria.RECEITA, parent_id=parent.id
                ),
                u_id,
            )

    async def test_parent_de_outro_usuario_falha(
        self, svc: CategoriaService, mock_repo: AsyncMock
    ) -> None:
        parent = _make_cat(nivel=1, usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = parent
        mock_repo.tem_acesso.return_value = False

        with pytest.raises(PermissionDeniedError):
            await svc.criar(
                CategoriaCreate(
                    nome="Sub", tipo=TipoCategoria.RECEITA, parent_id=parent.id
                ),
                uuid.uuid4(),
            )


class TestInativar:
    async def test_ja_inativa_falha(self, svc: CategoriaService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        cat = _make_cat(ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = cat

        with pytest.raises(ConflictError, match="já está inativa"):
            await svc.inativar(cat.id, u_id)

    async def test_com_filhos_ativos_falha(
        self, svc: CategoriaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cat = _make_cat(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = cat
        mock_repo.has_filhos_ativos.return_value = True

        with pytest.raises(DomainError, match="subcategorias ativas"):
            await svc.inativar(cat.id, u_id)

    async def test_inativa_com_sucesso(
        self, svc: CategoriaService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        cat = _make_cat(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = cat
        mock_repo.has_filhos_ativos.return_value = False
        mock_repo.has_lancamentos.return_value = False

        result = await svc.inativar(cat.id, u_id)
        assert result.ativa is False


class TestPlanopadrao:
    async def test_ja_inicializado_falha(
        self, svc: CategoriaService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.ja_inicializou_plano.return_value = True
        with pytest.raises(ConflictError, match="já foi inicializado"):
            await svc.inicializar_plano_padrao(uuid.uuid4())

    async def test_cria_categorias(self, svc: CategoriaService, mock_repo: AsyncMock) -> None:
        mock_repo.ja_inicializou_plano.return_value = False
        mock_repo.create.side_effect = lambda c: c

        total = await svc.inicializar_plano_padrao(uuid.uuid4())
        assert total > 0
        assert mock_repo.create.await_count == total


class TestConstruirArvore:
    def test_arvore_simples(self) -> None:
        u_id = uuid.uuid4()
        pai = _make_cat(nivel=1, usuario_id=u_id)
        filho = _make_cat(nivel=2, usuario_id=u_id, parent_id=pai.id)
        pai.nome = "Pai"
        filho.nome = "Filho"
        pai.codigo = None
        filho.codigo = None

        arvore = _construir_arvore([pai, filho])

        assert len(arvore) == 1
        assert len(arvore[0].filhos) == 1
        assert arvore[0].filhos[0].nome == "Filho"

    def test_sem_categorias(self) -> None:
        assert _construir_arvore([]) == []
