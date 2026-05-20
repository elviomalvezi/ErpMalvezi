import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class StatusTransferencia(enum.StrEnum):
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class Transferencia(BaseModel):
    __tablename__ = "transferencia"
    __table_args__ = (
        Index("ix_transferencia_empresa_origem", "empresa_origem_id"),
        Index("ix_transferencia_empresa_destino", "empresa_destino_id"),
        Index("ix_transferencia_data", "data_transferencia"),
        Index("ix_transferencia_conta_origem", "conta_origem_id"),
        Index("ix_transferencia_conta_destino", "conta_destino_id"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    empresa_origem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    empresa_destino_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    conta_origem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conta_bancaria.id", ondelete="RESTRICT"), nullable=False
    )
    conta_destino_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conta_bancaria.id", ondelete="RESTRICT"), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    data_transferencia: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[StatusTransferencia] = mapped_column(
        Enum(StatusTransferencia, name="status_transferencia", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusTransferencia.CONCLUIDA,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
