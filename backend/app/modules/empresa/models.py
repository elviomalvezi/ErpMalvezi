import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class TipoPessoa(enum.StrEnum):
    PJ = "PJ"
    PF = "PF"


class RegimeTributario(enum.StrEnum):
    SIMPLES = "Simples"
    PRESUMIDO = "Presumido"
    REAL = "Real"
    MEI = "MEI"


class Empresa(BaseModel):
    __tablename__ = "empresa"

    tipo: Mapped[TipoPessoa] = mapped_column(
        Enum(TipoPessoa, name="tipo_pessoa", create_type=False), nullable=False
    )
    documento: Mapped[str] = mapped_column(String(18), unique=True, nullable=False)
    nome_principal: Mapped[str] = mapped_column(String(200), nullable=False)
    nome_alternativo: Mapped[str | None] = mapped_column(String(200))
    documento_complementar_1: Mapped[str | None] = mapped_column(String(30))
    documento_complementar_2: Mapped[str | None] = mapped_column(String(30))
    regime_tributario: Mapped[RegimeTributario | None] = mapped_column(
        Enum(RegimeTributario, name="regime_tributario", create_type=False, values_callable=lambda obj: [e.value for e in obj])
    )

    # Configurações monetárias
    moeda_padrao: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    simbolo_monetario: Mapped[str] = mapped_column(String(5), default="R$", nullable=False)
    separador_decimal: Mapped[str] = mapped_column(String(1), default=",", nullable=False)
    separador_milhares: Mapped[str] = mapped_column(String(1), default=".", nullable=False)
    casas_decimais_valor: Mapped[int] = mapped_column(SmallInteger, default=2, nullable=False)
    casas_decimais_percentual: Mapped[int] = mapped_column(SmallInteger, default=2, nullable=False)

    # Configurações financeiras
    mes_inicio_exercicio: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    trava_fechamento_ativa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dia_fechamento_mensal: Mapped[int] = mapped_column(SmallInteger, default=5, nullable=False)
    prefixo_lancamento: Mapped[str] = mapped_column(String(10), default="LCT-", nullable=False)
    proximo_numero_lancamento: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    reset_anual_numeracao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_inicio_uso: Mapped[str | None] = mapped_column(Date)

    # Identidade visual
    cor_primaria: Mapped[str | None] = mapped_column(String(7))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    email_remetente_nome: Mapped[str | None] = mapped_column(String(200))
    email_assinatura: Mapped[str | None] = mapped_column(Text)
    mensagem_padrao_boleto: Mapped[str | None] = mapped_column(Text)

    # Endereço
    endereco_cep: Mapped[str | None] = mapped_column(String(9))
    logradouro: Mapped[str | None] = mapped_column(String(200))
    numero: Mapped[str | None] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(100))
    uf: Mapped[str | None] = mapped_column(String(2))
    pais: Mapped[str] = mapped_column(String(50), default="Brasil", nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(320))

    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="SET NULL")
    )

    usuarios: Mapped[list["UsuarioEmpresa"]] = relationship(
        "UsuarioEmpresa", back_populates="empresa", lazy="noload"
    )


class UsuarioEmpresa(BaseModel):
    __tablename__ = "usuario_empresa"
    __table_args__ = (UniqueConstraint("usuario_id", "empresa_id", name="uq_usuario_empresa"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="usuarios", lazy="noload")
