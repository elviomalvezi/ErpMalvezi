class DomainError(Exception):
    """Erro de regra de negócio — convertido em HTTP 422 no router."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Recurso não encontrado — convertido em HTTP 404 no router."""


class PermissionDeniedError(DomainError):
    """Acesso negado — convertido em HTTP 403 no router."""


class ConflictError(DomainError):
    """Conflito de dados (ex: documento duplicado) — HTTP 409."""
