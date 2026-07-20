import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class TipoToken(enum.StrEnum):
    RECUPERACAO_SENHA = "recuperacao_senha"
    VERIFICACAO_EMAIL = "verificacao_email"


class Usuario(BaseModel):
    __tablename__ = "usuario"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    foto_url: Mapped[str | None] = mapped_column(String(500))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gestor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferencia_multi_empresa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Incrementado para revogar todos os tokens do usuário (inativar, troca de senha).
    # O token carrega o valor em `tv`; cada request compara com este.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")


class TokenSeguranca(BaseModel):
    __tablename__ = "token_seguranca"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Sessao(BaseModel):
    __tablename__ = "sessao"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_origem: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))


class TentativaLogin(BaseModel):
    __tablename__ = "tentativa_login"
    __table_args__ = (Index("ix_tentativa_login_email_criado_em", "email", "criado_em"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    ip_origem: Mapped[str | None] = mapped_column(String(45))
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False)
