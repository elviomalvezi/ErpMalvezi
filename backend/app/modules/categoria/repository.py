import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.modules.categoria.models import Categoria, EscopoCategoria
from app.modules.empresa.models import UsuarioEmpresa


class CategoriaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # --- helpers de acesso por empresa ----------------------------------------

    def _sq_empresas(self, usuario_id: uuid.UUID) -> Select:
        return select(UsuarioEmpresa.empresa_id).where(
            UsuarioEmpresa.usuario_id == usuario_id
        )

    def _acesso_cond(self, usuario_id: uuid.UUID):
        """Membro de empresa acessa dados específicos dessa empresa + todos os globais."""
        sq_empresas = self._sq_empresas(usuario_id)
        return or_(
            Categoria.empresa_id.in_(sq_empresas),
            Categoria.empresa_id.is_(None),
        )

    # --------------------------------------------------------------------------

    async def get_by_id(self, categoria_id: uuid.UUID) -> Categoria | None:
        result = await self._db.execute(
            select(Categoria).where(Categoria.id == categoria_id)
        )
        return result.scalar_one_or_none()

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        apenas_ativas: bool = True,
    ) -> list[Categoria]:
        """Retorna categorias acessíveis ao usuário via vínculo de empresa."""
        filtros = [self._acesso_cond(usuario_id)]

        if empresa_id is not None:
            filtros.append(
                or_(
                    Categoria.empresa_id.is_(None),
                    Categoria.empresa_id == empresa_id,
                )
            )
        else:
            filtros.append(Categoria.empresa_id.is_(None))

        if apenas_ativas:
            filtros.append(Categoria.ativa.is_(True))

        result = await self._db.execute(
            select(Categoria)
            .where(and_(*filtros))
            .order_by(Categoria.tipo, Categoria.nivel, Categoria.nome)
        )
        return list(result.scalars())

    async def tem_acesso(self, categoria_id: uuid.UUID, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Categoria.id).where(
                Categoria.id == categoria_id,
                self._acesso_cond(usuario_id),
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_nome(
        self,
        nome: str,
        tipo: str,
        usuario_id: uuid.UUID,
    ) -> Categoria | None:
        result = await self._db.execute(
            select(Categoria).where(
                self._acesso_cond(usuario_id),
                Categoria.nome.ilike(nome),
                Categoria.tipo == tipo,
                Categoria.ativa.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def has_filhos_ativos(self, categoria_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Categoria.id).where(
                Categoria.parent_id == categoria_id,
                Categoria.ativa.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None

    async def has_lancamentos(self, categoria_id: uuid.UUID) -> bool:
        # Placeholder — implementado no Módulo 9
        return False

    async def create(self, categoria: Categoria) -> Categoria:
        self._db.add(categoria)
        await self._db.flush()
        return categoria

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Categoria) -> None:
        await self._db.refresh(obj)

    async def ja_inicializou_plano(self, usuario_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(Categoria.id).where(
                self._acesso_cond(usuario_id),
                Categoria.escopo == EscopoCategoria.GLOBAL,
            )
        )
        return result.scalar_one_or_none() is not None
