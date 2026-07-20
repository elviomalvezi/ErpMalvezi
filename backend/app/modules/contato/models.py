import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoContato(enum.StrEnum):
    PJ = "PJ"
    PF = "PF"


class EscopoContato(enum.StrEnum):
    GLOBAL = "global"
    ESPECIFICO = "especifico"


class Contato(BaseModel):
    __tablename__ = "contato"
    __table_args__ = (
        # Por empresa: o mesmo CNPJ pode existir em empresas diferentes (cada uma
        # com seu cadastro), mas não duplicado dentro da mesma empresa.
        UniqueConstraint(
            "usuario_id", "empresa_id", "documento", name="uq_contato_usuario_empresa_documento"
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=True
    )
    tipo: Mapped[TipoContato] = mapped_column(
        Enum(TipoContato, name="tipo_contato", create_type=False), nullable=False
    )
    documento: Mapped[str | None] = mapped_column(String(14), nullable=True)
    nome_principal: Mapped[str] = mapped_column(String(200), nullable=False)
    nome_alternativo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    eh_cliente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    eh_fornecedor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escopo: Mapped[str] = mapped_column(
        String(12), nullable=False, server_default="global"
    )

    # Contato
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    celular: Mapped[str | None] = mapped_column(String(20), nullable=True)
    site: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Endereço
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    logradouro: Mapped[str | None] = mapped_column(String(200), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(10), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    pais: Mapped[str] = mapped_column(String(50), default="Brasil", nullable=False)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
