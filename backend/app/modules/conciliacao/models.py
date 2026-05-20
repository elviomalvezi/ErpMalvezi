import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel
from app.modules.lancamento.models import TipoLancamento


class StatusImportacao(enum.StrEnum):
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    ERRO = "erro"


class StatusTransacao(enum.StrEnum):
    PENDENTE = "pendente"
    CONCILIADA = "conciliada"
    IGNORADA = "ignorada"


class TipoTransacao(enum.StrEnum):
    CREDITO = "credito"
    DEBITO = "debito"


class ImportacaoBancaria(BaseModel):
    __tablename__ = "importacao_bancaria"

    conta_bancaria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conta_bancaria.id", ondelete="CASCADE"),
        nullable=False,
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome_arquivo: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[StatusImportacao] = mapped_column(
        Enum(StatusImportacao, name="status_importacao", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusImportacao.CONCLUIDA,
    )
    total_transacoes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conciliadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ignoradas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TransacaoBancaria(BaseModel):
    __tablename__ = "transacao_bancaria"
    __table_args__ = (
        Index("ix_transacao_importacao", "importacao_id"),
        Index("ix_transacao_conta", "conta_bancaria_id"),
        Index("ix_transacao_data", "data"),
        Index("ix_transacao_status", "status"),
    )

    importacao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("importacao_bancaria.id", ondelete="CASCADE"),
        nullable=False,
    )
    conta_bancaria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conta_bancaria.id", ondelete="CASCADE"),
        nullable=False,
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    id_externo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tipo: Mapped[TipoTransacao] = mapped_column(
        Enum(TipoTransacao, name="tipo_transacao", create_type=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    descricao_original: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[StatusTransacao] = mapped_column(
        Enum(StatusTransacao, name="status_transacao", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusTransacao.PENDENTE,
    )
    lancamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lancamento.id", ondelete="SET NULL"),
        nullable=True,
    )


class RegraCategorizacao(BaseModel):
    __tablename__ = "regra_categorizacao"
    __table_args__ = (
        UniqueConstraint("usuario_id", "padrao", name="uq_regra_usuario_padrao"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    padrao: Mapped[str] = mapped_column(String(300), nullable=False)
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=True
    )
    tipo_lancamento: Mapped[TipoLancamento | None] = mapped_column(
        Enum(TipoLancamento, name="tipo_lancamento", create_type=False), nullable=True
    )
    contato_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contato.id", ondelete="SET NULL"), nullable=True
    )
    contador: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
