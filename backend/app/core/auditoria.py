"""Registro de auditoria para alterações em dados financeiros."""
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

import structlog
from sqlalchemy import event
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.utils import new_uuid

logger = structlog.get_logger()

# Contexto que carrega o usuario_id da requisição atual
_usuario_ctx: ContextVar[uuid.UUID | None] = ContextVar("usuario_auditoria", default=None)


def set_usuario_auditoria(usuario_id: uuid.UUID | None) -> None:
    _usuario_ctx.set(usuario_id)


def get_usuario_auditoria() -> uuid.UUID | None:
    return _usuario_ctx.get()


# Tabelas que devem ser auditadas
_TABELAS_AUDITADAS = {
    "lancamento",
    "transferencia",
    "usuario_permissao",
}


def _serializar(obj: object) -> object:
    """Serializa valores para JSON de forma segura."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def _row_to_dict(instance: object) -> dict:
    """Converte uma instância SQLAlchemy em dict serializável."""
    mapper = instance.__mapper__  # type: ignore[union-attr]
    return {
        col.key: _serializar(getattr(instance, col.key))
        for col in mapper.column_attrs
    }


def registrar_listeners(session_factory) -> None:  # type: ignore[no-untyped-def]
    """Registra event listeners no session factory para auditoria automática."""

    @event.listens_for(session_factory, "before_flush")
    def before_flush(session: Session, flush_context, instances):  # type: ignore[no-untyped-def]
        from app.modules.auditoria.models import Auditoria

        usuario_id = get_usuario_auditoria()
        agora = datetime.now(timezone.utc)
        entradas: list[Auditoria] = []

        for obj in session.new:
            tabela = getattr(obj, "__tablename__", None)
            if tabela not in _TABELAS_AUDITADAS:
                continue
            # O id usa default client-side (new_uuid), avaliado só no flush — ou seja,
            # ainda é None neste before_flush. Geramos agora para que registro_id
            # (NOT NULL) e o snapshot fiquem corretos; o INSERT reaproveita este id.
            if getattr(obj, "id", None) is None:
                obj.id = new_uuid()  # type: ignore[union-attr]
            entradas.append(Auditoria(
                id=new_uuid(),
                tabela=tabela,
                registro_id=obj.id,  # type: ignore[union-attr]
                acao="insert",
                usuario_id=usuario_id,
                valor_anterior=None,
                valor_novo=_row_to_dict(obj),
                criado_em=agora,
            ))

        for obj in session.dirty:
            tabela = getattr(obj, "__tablename__", None)
            if tabela not in _TABELAS_AUDITADAS:
                continue
            # Captura apenas as colunas que mudaram (SQLAlchemy 2.x: histórico via
            # estado do objeto inspecionado, não via InstrumentedAttribute).
            state = sa_inspect(obj)
            col_keys = {c.key for c in obj.__mapper__.column_attrs}  # type: ignore[union-attr]
            alteracoes: dict = {}
            for attr in state.attrs:
                if attr.key not in col_keys:
                    continue
                hist = attr.history
                if hist.has_changes():
                    alteracoes[attr.key] = {
                        "antes": _serializar(hist.deleted[0]) if hist.deleted else None,
                        "depois": _serializar(hist.added[0]) if hist.added else None,
                    }
            if alteracoes:
                entradas.append(Auditoria(
                    id=new_uuid(),
                    tabela=tabela,
                    registro_id=obj.id,  # type: ignore[union-attr]
                    acao="update",
                    usuario_id=usuario_id,
                    valor_anterior={k: v["antes"] for k, v in alteracoes.items()},
                    valor_novo={k: v["depois"] for k, v in alteracoes.items()},
                    criado_em=agora,
                ))

        for obj in session.deleted:
            tabela = getattr(obj, "__tablename__", None)
            if tabela not in _TABELAS_AUDITADAS:
                continue
            entradas.append(Auditoria(
                id=new_uuid(),
                tabela=tabela,
                registro_id=obj.id,  # type: ignore[union-attr]
                acao="delete",
                usuario_id=usuario_id,
                valor_anterior=_row_to_dict(obj),
                valor_novo=None,
                criado_em=agora,
            ))

        for entrada in entradas:
            session.add(entrada)
