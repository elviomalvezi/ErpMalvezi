import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class StatusFatura(enum.StrEnum):
    ABERTA = "aberta"
    FECHADA = "fechada"
    PAGA = "paga"


class Fatura(BaseModel):
    __tablename__ = "fatura"
    __table_args__ = (
        UniqueConstraint(
            "conta_bancaria_id", "competencia", name="uq_fatura_conta_competencia"
        ),
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
    # Primeiro dia do mês de referência (ex: 2024-01-01 para janeiro)
    competencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_fechamento: Mapped[date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StatusFatura] = mapped_column(
        Enum(StatusFatura, name="status_fatura", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusFatura.ABERTA,
    )
    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    valor_pago: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Conta usada para pagar a fatura
    conta_pagamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conta_bancaria.id", ondelete="SET NULL"),
        nullable=True,
    )
