import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class StatusVeiculo(enum.StrEnum):
    ATIVO = "ativo"
    VENDIDO = "vendido"
    SINISTRADO = "sinistrado"
    INATIVO = "inativo"


class CombustivelVeiculo(enum.StrEnum):
    GASOLINA = "gasolina"
    ETANOL = "etanol"
    FLEX = "flex"
    DIESEL = "diesel"
    ELETRICO = "eletrico"
    HIBRIDO = "hibrido"
    GNV = "gnv"


class TipoImovel(enum.StrEnum):
    CASA = "casa"
    APARTAMENTO = "apartamento"
    TERRENO = "terreno"
    SALA_COMERCIAL = "sala_comercial"
    GALPAO = "galpao"
    LOJA = "loja"
    OUTRO = "outro"


class StatusImovel(enum.StrEnum):
    ATIVO = "ativo"
    LOCADO = "locado"
    VENDIDO = "vendido"
    EM_REFORMA = "em_reforma"
    INATIVO = "inativo"


class Veiculo(BaseModel):
    __tablename__ = "veiculo"
    __table_args__ = (
        Index("ix_veiculo_empresa", "empresa_id"),
        Index("ix_veiculo_usuario", "usuario_id"),
    )

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    placa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    renavam: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chassi: Mapped[str | None] = mapped_column(String(50), nullable=True)
    numero_motor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marca: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str] = mapped_column(String(150), nullable=False)
    ano_fabricacao: Mapped[int] = mapped_column(Integer, nullable=False)
    ano_modelo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    combustivel: Mapped[CombustivelVeiculo | None] = mapped_column(
        Enum(CombustivelVeiculo, name="combustivel_veiculo", create_type=False), nullable=True
    )
    valor_aquisicao: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    data_aquisicao: Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_mercado: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    quilometragem: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[StatusVeiculo] = mapped_column(
        Enum(StatusVeiculo, name="status_veiculo", create_type=False,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusVeiculo.ATIVO,
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Imovel(BaseModel):
    __tablename__ = "imovel"
    __table_args__ = (
        Index("ix_imovel_empresa", "empresa_id"),
        Index("ix_imovel_usuario", "usuario_id"),
    )

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[TipoImovel] = mapped_column(
        Enum(TipoImovel, name="tipo_imovel", create_type=False,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    matricula: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inscricao_municipal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    logradouro: Mapped[str | None] = mapped_column(String(300), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(10), nullable=True)
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    area_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    area_construida: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    valor_aquisicao: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    data_aquisicao: Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_mercado: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    valor_venal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[StatusImovel] = mapped_column(
        Enum(StatusImovel, name="status_imovel", create_type=False,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=StatusImovel.ATIVO,
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class VeiculoAnexo(BaseModel):
    __tablename__ = "veiculo_anexo"
    __table_args__ = (Index("ix_veiculo_anexo_veiculo", "veiculo_id"),)

    veiculo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("veiculo.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    caminho: Mapped[str] = mapped_column(String(500), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ImovelAnexo(BaseModel):
    __tablename__ = "imovel_anexo"
    __table_args__ = (Index("ix_imovel_anexo_imovel", "imovel_id"),)

    imovel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("imovel.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    caminho: Mapped[str] = mapped_column(String(500), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
