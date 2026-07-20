from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    connect_args={"ssl": False} if settings.is_development else {},
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Ativa a auditoria automática (before_flush). A AsyncSession delega o flush
# para uma Session síncrona, então o listener é registrado na classe Session.
from app.core.auditoria import registrar_listeners  # noqa: E402

registrar_listeners(Session)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
