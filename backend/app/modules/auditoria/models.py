import uuid

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Auditoria(BaseModel):
    __tablename__ = "auditoria"
    __table_args__ = (
        Index("ix_auditoria_tabela_registro", "tabela", "registro_id"),
        Index("ix_auditoria_usuario", "usuario_id"),
    )

    tabela: Mapped[str] = mapped_column(String(100), nullable=False)
    registro_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    acao: Mapped[str] = mapped_column(String(10), nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    valor_anterior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valor_novo: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # criado_em / atualizado_em herdados de BaseModel (server_default=func.now()).
