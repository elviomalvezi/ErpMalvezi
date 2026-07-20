import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, LargeBinary, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoLancamento(enum.StrEnum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"


class StatusLancamento(enum.StrEnum):
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    NAO_REALIZADO = "nao_realizado"


class FrequenciaRecorrencia(enum.StrEnum):
    SEMANAL = "semanal"
    QUINZENAL = "quinzenal"
    MENSAL = "mensal"
    ANUAL = "anual"


class Lancamento(BaseModel):
    __tablename__ = "lancamento"
    __table_args__ = (
        Index("ix_lancamento_empresa_vencimento", "empresa_id", "data_vencimento"),
        Index("ix_lancamento_status", "status"),
        Index("ix_lancamento_categoria", "categoria_id"),
        Index("ix_lancamento_contato", "contato_id"),
        Index("ix_lancamento_grupo", "grupo_parcelas_id"),
        Index("ix_lancamento_recorrencia", "recorrencia_id"),
        Index("ix_lancamento_saldo", "conta_bancaria_id", "status", "data_vencimento"),
    )

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[TipoLancamento] = mapped_column(
        Enum(TipoLancamento, name="tipo_lancamento", create_type=False), nullable=False
    )
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    data_competencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusLancamento] = mapped_column(
        Enum(StatusLancamento, name="status_lancamento", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusLancamento.PENDENTE,
    )
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categoria.id", ondelete="RESTRICT"), nullable=True
    )
    contato_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contato.id", ondelete="RESTRICT"), nullable=True
    )
    # Conta usada no pagamento (pode ser diferente da conta do lançamento)
    conta_bancaria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conta_bancaria.id", ondelete="RESTRICT"), nullable=True
    )
    # Fatura do cartão (preenchido automaticamente quando conta é cartão de crédito)
    fatura_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fatura.id", ondelete="RESTRICT"), nullable=True
    )
    # Parcelamento
    numero_parcela: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    total_parcelas: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    grupo_parcelas_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # Recorrência
    recorrencia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False, default=list, server_default="{}")
    veiculo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("veiculo.id", ondelete="SET NULL"), nullable=True
    )
    imovel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("imovel.id", ondelete="SET NULL"), nullable=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LancamentoAnexo(BaseModel):
    __tablename__ = "lancamento_anexo"
    __table_args__ = (Index("ix_lancamento_anexo_lancamento", "lancamento_id"),)

    lancamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lancamento.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Conteúdo do anexo armazenado no próprio banco (BYTEA) — garante persistência
    # e backup consistente via pg_dump. `caminho` fica como legado/opcional.
    conteudo: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    caminho: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
