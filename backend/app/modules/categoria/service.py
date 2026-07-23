import uuid
from typing import TypedDict

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from app.modules.categoria.models import Categoria, EscopoCategoria
from app.modules.categoria.repository import CategoriaRepository
from app.modules.categoria.schemas import (
    CategoriaCreate,
    CategoriaTreeNode,
    CategoriaUpdate,
)

logger = structlog.get_logger()

MAX_NIVEL = 3


class _PlanoItem(TypedDict):
    tipo: str
    nome: str
    parent: str | None


_PLANO_PADRAO: list[_PlanoItem] = [
    # ── RECEITAS ────────────────────────────────────────────────────────────
    {"tipo": "RECEITA", "nome": "Receitas Operacionais", "parent": None},
    {"tipo": "RECEITA", "nome": "Vendas de Produtos", "parent": "Receitas Operacionais"},
    {"tipo": "RECEITA", "nome": "Produtos", "parent": "Vendas de Produtos"},
    {"tipo": "RECEITA", "nome": "Prestação de Serviços", "parent": "Receitas Operacionais"},
    {"tipo": "RECEITA", "nome": "Serviços", "parent": "Prestação de Serviços"},
    {"tipo": "RECEITA", "nome": "Receitas Financeiras", "parent": "Receitas Operacionais"},
    {"tipo": "RECEITA", "nome": "Juros Recebidos", "parent": "Receitas Financeiras"},
    {"tipo": "RECEITA", "nome": "Rendimentos de Aplicações", "parent": "Receitas Financeiras"},
    {"tipo": "RECEITA", "nome": "Outras Receitas", "parent": None},
    {"tipo": "RECEITA", "nome": "Receitas Diversas", "parent": "Outras Receitas"},
    # ── DESPESAS ─────────────────────────────────────────────────────────────
    {"tipo": "DESPESA", "nome": "Despesas Operacionais", "parent": None},
    {"tipo": "DESPESA", "nome": "Pessoal", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Salários e Pró-labore", "parent": "Pessoal"},
    {"tipo": "DESPESA", "nome": "Encargos Sociais", "parent": "Pessoal"},
    {"tipo": "DESPESA", "nome": "Benefícios", "parent": "Pessoal"},
    {"tipo": "DESPESA", "nome": "Infraestrutura", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Aluguel", "parent": "Infraestrutura"},
    {"tipo": "DESPESA", "nome": "Água e Energia", "parent": "Infraestrutura"},
    {"tipo": "DESPESA", "nome": "Internet e Telefone", "parent": "Infraestrutura"},
    {"tipo": "DESPESA", "nome": "Manutenção e Conservação", "parent": "Infraestrutura"},
    {"tipo": "DESPESA", "nome": "Materiais e Suprimentos", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Material de Escritório", "parent": "Materiais e Suprimentos"},
    {"tipo": "DESPESA", "nome": "Marketing e Vendas", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Publicidade e Propaganda", "parent": "Marketing e Vendas"},
    {"tipo": "DESPESA", "nome": "Comissões de Vendas", "parent": "Marketing e Vendas"},
    {"tipo": "DESPESA", "nome": "Tecnologia", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Software e Assinaturas", "parent": "Tecnologia"},
    {"tipo": "DESPESA", "nome": "Hardware e Equipamentos", "parent": "Tecnologia"},
    {"tipo": "DESPESA", "nome": "Serviços Profissionais", "parent": "Despesas Operacionais"},
    {"tipo": "DESPESA", "nome": "Contabilidade", "parent": "Serviços Profissionais"},
    {"tipo": "DESPESA", "nome": "Assessoria Jurídica", "parent": "Serviços Profissionais"},
    {"tipo": "DESPESA", "nome": "Consultoria", "parent": "Serviços Profissionais"},
    {"tipo": "DESPESA", "nome": "Despesas Financeiras", "parent": None},
    {"tipo": "DESPESA", "nome": "Encargos Financeiros", "parent": "Despesas Financeiras"},
    {"tipo": "DESPESA", "nome": "Juros e Multas", "parent": "Encargos Financeiros"},
    {"tipo": "DESPESA", "nome": "Tarifas Bancárias", "parent": "Encargos Financeiros"},
    {"tipo": "DESPESA", "nome": "IOF e Tributação Financeira", "parent": "Encargos Financeiros"},
    {"tipo": "DESPESA", "nome": "Impostos e Tributos", "parent": None},
    {"tipo": "DESPESA", "nome": "Tributos Federais", "parent": "Impostos e Tributos"},
    {"tipo": "DESPESA", "nome": "IRPJ / CSLL", "parent": "Tributos Federais"},
    {"tipo": "DESPESA", "nome": "PIS / COFINS", "parent": "Tributos Federais"},
    {"tipo": "DESPESA", "nome": "Simples Nacional", "parent": "Tributos Federais"},
    {"tipo": "DESPESA", "nome": "Tributos Estaduais", "parent": "Impostos e Tributos"},
    {"tipo": "DESPESA", "nome": "ICMS", "parent": "Tributos Estaduais"},
    {"tipo": "DESPESA", "nome": "Tributos Municipais", "parent": "Impostos e Tributos"},
    {"tipo": "DESPESA", "nome": "ISS", "parent": "Tributos Municipais"},
    {"tipo": "DESPESA", "nome": "Outras Despesas", "parent": None},
    {"tipo": "DESPESA", "nome": "Despesas Diversas", "parent": "Outras Despesas"},
]


class CategoriaService:
    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        apenas_ativas: bool = True,
    ) -> list[Categoria]:
        return await self._repo.listar(usuario_id, empresa_id, apenas_ativas)

    async def listar_arvore(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
    ) -> list[CategoriaTreeNode]:
        categorias = await self._repo.listar(usuario_id, empresa_id)
        return _construir_arvore(categorias)

    async def obter(self, categoria_id: uuid.UUID, usuario_id: uuid.UUID) -> Categoria:
        cat = await self._repo.get_by_id(categoria_id)
        if cat is None:
            raise NotFoundError("Categoria não encontrada.")
        if not await self._repo.tem_acesso(categoria_id, usuario_id):
            raise PermissionDeniedError("Sem acesso a esta categoria.")
        return cat

    async def criar(self, data: CategoriaCreate, usuario_id: uuid.UUID) -> Categoria:
        nivel = 1
        parent_id = data.parent_id

        if parent_id is not None:
            parent = await self._repo.get_by_id(parent_id)
            if parent is None:
                raise NotFoundError("Categoria pai não encontrada.")
            if not await self._repo.tem_acesso(parent_id, usuario_id):
                raise PermissionDeniedError("Sem acesso à categoria pai.")
            if not parent.ativa:
                raise DomainError("Categoria pai está inativa.")
            nivel = parent.nivel + 1
            if nivel > MAX_NIVEL:
                raise DomainError(
                    f"Hierarquia máxima de {MAX_NIVEL} níveis atingida."
                )

        categoria = Categoria(
            usuario_id=usuario_id,
            empresa_id=data.empresa_id,
            parent_id=parent_id,
            nome=data.nome,
            tipo=data.tipo,
            escopo=data.escopo,
            nivel=nivel,
            codigo=data.codigo,
            descricao=data.descricao,
            exigir_veiculo=data.exigir_veiculo,
            exigir_imovel=data.exigir_imovel,
        )
        await self._repo.create(categoria)
        await self._repo.commit()
        await self._repo.refresh(categoria)
        logger.info("categoria_criada", nome=data.nome, nivel=nivel, usuario_id=str(usuario_id))
        return categoria

    async def atualizar(
        self, categoria_id: uuid.UUID, data: CategoriaUpdate, usuario_id: uuid.UUID
    ) -> Categoria:
        cat = await self.obter(categoria_id, usuario_id)
        update_data = data.model_dump(exclude_unset=True)

        if "parent_id" in update_data:
            novo_parent_id = update_data.pop("parent_id")
            if novo_parent_id is None:
                cat.parent_id = None
                cat.nivel = 1
            else:
                if novo_parent_id == categoria_id:
                    raise DomainError("Uma categoria não pode ser pai de si mesma.")
                parent = await self._repo.get_by_id(novo_parent_id)
                if parent is None:
                    raise NotFoundError("Categoria pai não encontrada.")
                if not await self._repo.tem_acesso(novo_parent_id, usuario_id):
                    raise PermissionDeniedError("Sem acesso à categoria pai.")
                if parent.tipo != cat.tipo:
                    raise DomainError("A categoria pai deve ter o mesmo tipo (Receita/Despesa).")
                if parent.nivel >= 3:
                    raise DomainError("Não é possível criar subcategorias além do 3.º nível.")
                if await self._repo.has_filhos_ativos(categoria_id) and parent.nivel >= 2:
                    raise DomainError("Mover esta categoria criaria subcategorias além do 3.º nível.")
                cat.parent_id = novo_parent_id
                cat.nivel = parent.nivel + 1

        for field, value in update_data.items():
            setattr(cat, field, value)
        await self._repo.commit()
        await self._repo.refresh(cat)
        return cat

    async def inativar(self, categoria_id: uuid.UUID, usuario_id: uuid.UUID) -> Categoria:
        cat = await self.obter(categoria_id, usuario_id)
        if not cat.ativa:
            raise ConflictError("Categoria já está inativa.")
        if await self._repo.has_filhos_ativos(categoria_id):
            raise DomainError("Não é possível inativar uma categoria com subcategorias ativas.")
        if await self._repo.has_lancamentos(categoria_id):
            raise DomainError("Não é possível inativar uma categoria com lançamentos vinculados.")
        cat.ativa = False
        await self._repo.commit()
        await self._repo.refresh(cat)
        logger.info("categoria_inativada", categoria_id=str(categoria_id))
        return cat

    async def reativar(self, categoria_id: uuid.UUID, usuario_id: uuid.UUID) -> Categoria:
        cat = await self.obter(categoria_id, usuario_id)
        if cat.ativa:
            raise ConflictError("Categoria já está ativa.")
        if cat.parent_id is not None:
            parent = await self._repo.get_by_id(cat.parent_id)
            if parent and not parent.ativa:
                raise DomainError("Não é possível reativar uma categoria cujo pai está inativo.")
        cat.ativa = True
        await self._repo.commit()
        await self._repo.refresh(cat)
        return cat

    async def inicializar_plano_padrao(self, usuario_id: uuid.UUID) -> int:
        if await self._repo.ja_inicializou_plano(usuario_id):
            raise ConflictError("Plano padrão já foi inicializado para este usuário.")

        criados: dict[str, Categoria] = {}
        count = 0

        for item in _PLANO_PADRAO:
            parent_id: uuid.UUID | None = None
            parent_nivel = 0

            if item["parent"] is not None:
                parent_cat = criados.get(item["parent"])
                if parent_cat is None:
                    logger.warning("plano_padrao_parent_nao_encontrado", parent=item["parent"])
                    continue
                parent_id = parent_cat.id
                parent_nivel = parent_cat.nivel

            cat = Categoria(
                usuario_id=usuario_id,
                empresa_id=None,
                parent_id=parent_id,
                nome=item["nome"],
                tipo=item["tipo"],
                escopo=EscopoCategoria.GLOBAL,
                nivel=parent_nivel + 1,
            )
            await self._repo.create(cat)
            criados[item["nome"]] = cat
            count += 1

        await self._repo.commit()
        logger.info("plano_padrao_inicializado", usuario_id=str(usuario_id), total=count)
        return count


    async def merge(
        self,
        origem_id: uuid.UUID,
        destino_id: uuid.UUID,
        usuario_id: uuid.UUID,
    ) -> Categoria:
        from sqlalchemy import update

        from app.modules.lancamento.models import Lancamento

        origem = await self.obter(origem_id, usuario_id)
        destino = await self.obter(destino_id, usuario_id)

        if origem_id == destino_id:
            raise DomainError("Origem e destino devem ser diferentes.")
        if origem.tipo != destino.tipo:
            raise DomainError("Só é possível unir categorias do mesmo tipo (RECEITA/DESPESA).")

        # Reassociar todos os lançamentos da origem para o destino
        await self._repo._db.execute(
            update(Lancamento)
            .where(Lancamento.categoria_id == origem_id)
            .values(categoria_id=destino_id)
        )

        # Reassociar subcategorias da origem para o destino
        await self._repo._db.execute(
            update(Categoria)
            .where(Categoria.parent_id == origem_id)
            .values(parent_id=destino_id)
        )

        # Inativar a categoria de origem
        origem.ativa = False
        await self._repo.commit()

        logger.info("categoria_merge", origem=str(origem_id), destino=str(destino_id))
        return destino


def _construir_arvore(categorias: list[Categoria]) -> list[CategoriaTreeNode]:
    nodes: dict[uuid.UUID, CategoriaTreeNode] = {}
    raizes: list[CategoriaTreeNode] = []

    for cat in categorias:
        node = CategoriaTreeNode(
            id=cat.id,
            parent_id=cat.parent_id,
            nome=cat.nome,
            tipo=cat.tipo,
            escopo=cat.escopo,
            nivel=cat.nivel,
            codigo=cat.codigo,
            exigir_veiculo=cat.exigir_veiculo,
            exigir_imovel=cat.exigir_imovel,
            ativa=cat.ativa,
            filhos=[],
        )
        nodes[cat.id] = node

    for cat in categorias:
        node = nodes[cat.id]
        if cat.parent_id is not None and cat.parent_id in nodes:
            nodes[cat.parent_id].filhos.append(node)
        else:
            raizes.append(node)

    return raizes
