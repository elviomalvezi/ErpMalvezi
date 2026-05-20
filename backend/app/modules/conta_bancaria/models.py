import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoConta(enum.StrEnum):
    CORRENTE = "corrente"
    POUPANCA = "poupanca"
    CAIXINHA = "caixinha"
    APLICACAO = "aplicacao"
    CARTAO_CREDITO = "cartao_credito"


class BandeiraCartao(enum.StrEnum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    ELO = "elo"
    AMEX = "amex"
    HIPERCARD = "hipercard"
    OUTRO = "outro"


class ContaBancaria(BaseModel):
    __tablename__ = "conta_bancaria"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoConta] = mapped_column(
        Enum(TipoConta, name="tipo_conta", create_type=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )

    # Dados bancários (opcionais para caixinha/aplicação/cartão)
    banco: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agencia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    numero_conta: Mapped[str | None] = mapped_column(String(30), nullable=True)
    digito: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Saldo inicial
    saldo_inicial: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    data_saldo_inicial: Mapped[str | None] = mapped_column(Date, nullable=True)

    # Campos exclusivos de cartão de crédito
    bandeira: Mapped[BandeiraCartao | None] = mapped_column(
        Enum(BandeiraCartao, name="bandeira_cartao", create_type=False, values_callable=lambda obj: [e.value for e in obj]), nullable=True
    )
    limite: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    dia_vencimento: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    dia_fechamento: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
