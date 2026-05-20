import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoCategoria(enum.StrEnum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"


class EscopoCategoria(enum.StrEnum):
    GLOBAL = "global"
    ESPECIFICO = "especifico"


class Categoria(BaseModel):
    __tablename__ = "categoria"
    __table_args__ = (
        Index("ix_categoria_usuario_tipo", "usuario_id", "tipo"),
        Index("ix_categoria_empresa", "empresa_id"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=True
    )

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    escopo: Mapped[str] = mapped_column(String(12), nullable=False, default="global")
    nivel: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    codigo: Mapped[str | None] = mapped_column(String(20))
    descricao: Mapped[str | None] = mapped_column(Text)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
