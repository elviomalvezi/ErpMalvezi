import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.contato.models import Contato, EscopoContato, TipoContato
from app.modules.contato.schemas import ContatoCreate, ContatoUpdate
from app.modules.contato.service import ContatoService

CPF_VALIDO = "52998224725"
CNPJ_VALIDO = "11222333000181"


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_repo: AsyncMock) -> ContatoService:
    return ContatoService(mock_repo)


def _make_contato(
    tipo: TipoContato = TipoContato.PF,
    ativa: bool = True,
    usuario_id: uuid.UUID | None = None,
    documento: str = CPF_VALIDO,
    escopo: EscopoContato = EscopoContato.GLOBAL,
    empresa_id: uuid.UUID | None = None,
) -> MagicMock:
    c = MagicMock(spec=Contato)
    c.id = uuid.uuid4()
    c.usuario_id = usuario_id or uuid.uuid4()
    c.tipo = tipo
    c.documento = documento
    c.nome_principal = "Contato Teste"
    c.nome_alternativo = None
    c.eh_cliente = True
    c.eh_fornecedor = False
    c.escopo = escopo
    c.empresa_id = empresa_id
    c.ativa = ativa
    return c


class TestCriar:
    async def test_cria_pf_sucesso(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        mock_repo.ja_existe_documento.return_value = False
        mock_repo.create.side_effect = lambda c: c

        contato = await svc.criar(
            ContatoCreate(
                tipo=TipoContato.PF,
                documento=CPF_VALIDO,
                nome_principal="João Silva",
            ),
            u_id,
        )
        assert contato.usuario_id == u_id
        assert contato.documento == CPF_VALIDO
        assert contato.tipo == TipoContato.PF

    async def test_cria_pj_sucesso(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        mock_repo.ja_existe_documento.return_value = False
        mock_repo.create.side_effect = lambda c: c

        contato = await svc.criar(
            ContatoCreate(
                tipo=TipoContato.PJ,
                documento=CNPJ_VALIDO,
                nome_principal="Empresa Ltda",
                eh_fornecedor=True,
            ),
            u_id,
        )
        assert contato.tipo == TipoContato.PJ
        assert contato.eh_fornecedor is True

    async def test_documento_duplicado_falha(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.ja_existe_documento.return_value = True

        with pytest.raises(ConflictError, match="Já existe um contato"):
            await svc.criar(
                ContatoCreate(
                    tipo=TipoContato.PF,
                    documento=CPF_VALIDO,
                    nome_principal="João",
                ),
                uuid.uuid4(),
            )


class TestObter:
    async def test_nao_encontrado(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await svc.obter(uuid.uuid4(), uuid.uuid4())

    async def test_outro_usuario_falha(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        contato = _make_contato(usuario_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = contato
        mock_repo.tem_acesso.return_value = False

        with pytest.raises(PermissionDeniedError):
            await svc.obter(contato.id, uuid.uuid4())


class TestAtualizar:
    async def test_atualiza_nome(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato

        await svc.atualizar(contato.id, ContatoUpdate(nome_principal="Novo Nome"), u_id)
        assert contato.nome_principal == "Novo Nome"

    async def test_remover_ambas_flags_falha(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(usuario_id=u_id)
        contato.eh_cliente = True
        contato.eh_fornecedor = False
        mock_repo.get_by_id.return_value = contato

        with pytest.raises(DomainError, match="cliente, fornecedor ou ambos"):
            await svc.atualizar(
                contato.id,
                ContatoUpdate(eh_cliente=False, eh_fornecedor=False),
                u_id,
            )

    async def test_documento_duplicado_falha(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(usuario_id=u_id, tipo=TipoContato.PF)
        mock_repo.get_by_id.return_value = contato
        mock_repo.ja_existe_documento.return_value = True

        with pytest.raises(ConflictError, match="outro contato"):
            await svc.atualizar(
                contato.id,
                ContatoUpdate(documento=CPF_VALIDO),
                u_id,
            )

    async def test_escopo_especifico_sem_empresa_falha(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(usuario_id=u_id, escopo=EscopoContato.GLOBAL)
        contato.empresa_id = None
        mock_repo.get_by_id.return_value = contato

        with pytest.raises(DomainError, match="empresa_id é obrigatório"):
            await svc.atualizar(
                contato.id,
                ContatoUpdate(escopo=EscopoContato.ESPECIFICO),
                u_id,
            )


class TestInativar:
    async def test_ja_inativo_falha(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato

        with pytest.raises(ConflictError, match="já está inativo"):
            await svc.inativar(contato.id, u_id)

    async def test_com_lancamentos_falha(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato
        mock_repo.has_lancamentos.return_value = True

        with pytest.raises(DomainError, match="lançamentos vinculados"):
            await svc.inativar(contato.id, u_id)

    async def test_inativa_com_sucesso(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato
        mock_repo.has_lancamentos.return_value = False

        result = await svc.inativar(contato.id, u_id)
        assert result.ativa is False


class TestReativar:
    async def test_ja_ativo_falha(self, svc: ContatoService, mock_repo: AsyncMock) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(ativa=True, usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato

        with pytest.raises(ConflictError, match="já está ativo"):
            await svc.reativar(contato.id, u_id)

    async def test_reativa_com_sucesso(
        self, svc: ContatoService, mock_repo: AsyncMock
    ) -> None:
        u_id = uuid.uuid4()
        contato = _make_contato(ativa=False, usuario_id=u_id)
        mock_repo.get_by_id.return_value = contato

        result = await svc.reativar(contato.id, u_id)
        assert result.ativa is True
