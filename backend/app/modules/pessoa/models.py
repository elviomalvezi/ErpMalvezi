import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoPessoa(enum.StrEnum):
    INTERNO = "interno"
    EXTERNO = "externo"


class Pessoa(BaseModel):
    __tablename__ = "pessoa"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    tipo: Mapped[TipoPessoa] = mapped_column(
        # 'pessoa_tipo' e não 'tipo_pessoa' — este último já existe (PJ/PF) e colide.
        Enum(TipoPessoa, name="pessoa_tipo", create_type=False,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    setor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    empresa_externa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PessoaCertificado(BaseModel):
    __tablename__ = "pessoa_certificado"
    __table_args__ = (
        UniqueConstraint("pessoa_id", "certificado_id", name="uq_pessoa_certificado"),
        Index("ix_pessoa_certificado_pessoa", "pessoa_id"),
        Index("ix_pessoa_certificado_certificado", "certificado_id"),
    )

    pessoa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    certificado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("certificado.id", ondelete="CASCADE"), nullable=False
    )
