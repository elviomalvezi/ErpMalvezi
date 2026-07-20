import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoCertificado(enum.StrEnum):
    E_CNPJ = "e_cnpj"
    E_CPF = "e_cpf"
    SSL = "ssl"
    OUTRO = "outro"


class Certificado(BaseModel):
    __tablename__ = "certificado"
    __table_args__ = (
        Index("ix_certificado_empresa", "empresa_id"),
        Index("ix_certificado_validade_fim", "validade_fim"),
    )

    # Empresa é opcional: nulo = certificado global (ex.: SSL de domínio do grupo).
    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="SET NULL"), nullable=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoCertificado] = mapped_column(
        Enum(TipoCertificado, name="tipo_certificado", create_type=False,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    # Metadados extraídos do certificado X.509
    titular: Mapped[str | None] = mapped_column(String(300), nullable=True)
    documento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emissor: Mapped[str | None] = mapped_column(String(300), nullable=True)
    numero_serie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    validade_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    validade_fim: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Arquivo e senha (a senha fica cifrada em repouso via Fernet/SECRET_KEY)
    formato: Mapped[str | None] = mapped_column(String(10), nullable=True)
    arquivo_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # deferred: o blob não é carregado na listagem, só quando acessado (download).
    arquivo: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    senha_cifrada: Mapped[str | None] = mapped_column(Text, nullable=True)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
