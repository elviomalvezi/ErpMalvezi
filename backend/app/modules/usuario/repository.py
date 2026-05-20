import hashlib
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.usuario.models import Sessao, TentativaLogin, TipoToken, TokenSeguranca, Usuario

MAX_TENTATIVAS = 5
LOCKOUT_MINUTES = 15


class UsuarioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        result = await self._db.execute(select(Usuario).where(Usuario.id == usuario_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self._db.execute(
            select(Usuario).where(func.lower(Usuario.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[Usuario]:
        result = await self._db.execute(select(Usuario).order_by(Usuario.nome))
        return result.scalars().all()

    async def create(self, usuario: Usuario) -> Usuario:
        self._db.add(usuario)
        await self._db.flush()
        return usuario

    async def commit(self) -> None:
        await self._db.commit()

    async def refresh(self, obj: Usuario) -> None:
        await self._db.refresh(obj)

    async def count_tentativas_recentes(self, email: str) -> int:
        cutoff = datetime.now(UTC) - timedelta(minutes=LOCKOUT_MINUTES)
        result = await self._db.execute(
            select(func.count(TentativaLogin.id)).where(
                func.lower(TentativaLogin.email) == email.lower(),
                TentativaLogin.sucesso.is_(False),
                TentativaLogin.criado_em >= cutoff,
            )
        )
        return result.scalar_one()

    async def registrar_tentativa(self, email: str, sucesso: bool, ip: str | None) -> None:
        tentativa = TentativaLogin(email=email.lower(), sucesso=sucesso, ip_origem=ip)
        self._db.add(tentativa)

    async def criar_sessao(self, sessao: Sessao) -> Sessao:
        self._db.add(sessao)
        await self._db.flush()
        return sessao

    async def get_sessao_by_jti(self, jti: str) -> Sessao | None:
        result = await self._db.execute(select(Sessao).where(Sessao.token_jti == jti))
        return result.scalar_one_or_none()

    async def revogar_sessao(self, jti: str) -> None:
        sessao = await self.get_sessao_by_jti(jti)
        if sessao and sessao.revogada_em is None:
            sessao.revogada_em = datetime.now(UTC)

    async def revogar_todas_sessoes_usuario(self, usuario_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(Sessao).where(
                Sessao.usuario_id == usuario_id,
                Sessao.revogada_em.is_(None),
            )
        )
        for sessao in result.scalars():
            sessao.revogada_em = datetime.now(UTC)

    async def criar_token(self, token: TokenSeguranca) -> TokenSeguranca:
        result = await self._db.execute(
            select(TokenSeguranca).where(
                TokenSeguranca.usuario_id == token.usuario_id,
                TokenSeguranca.tipo == token.tipo,
                TokenSeguranca.usado_em.is_(None),
            )
        )
        for old_token in result.scalars():
            old_token.usado_em = datetime.now(UTC)
        self._db.add(token)
        await self._db.flush()
        return token

    async def get_token_by_hash(self, token_hash: str, tipo: TipoToken) -> TokenSeguranca | None:
        result = await self._db.execute(
            select(TokenSeguranca).where(
                TokenSeguranca.token_hash == token_hash,
                TokenSeguranca.tipo == tipo,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
