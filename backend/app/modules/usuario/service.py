import secrets
import uuid
from datetime import UTC, datetime, timedelta

import structlog

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.core.utils import new_uuid
from app.infrastructure.email import smtp_sender
from app.modules.usuario.models import Sessao, TipoToken, TokenSeguranca, Usuario
from app.modules.usuario.repository import MAX_TENTATIVAS, UsuarioRepository
from app.modules.usuario.schemas import (
    AlterarSenhaRequest,
    DefinirSenhaRequest,
    LoginRequest,
    UsuarioCreate,
    UsuarioUpdate,
)

logger = structlog.get_logger()

TOKEN_RESET_EXPIRE_HOURS = 2
SESSION_EXPIRE_HOURS = 8


class AuthError(DomainError):
    pass


class ContaBloqueadaError(AuthError):
    pass


class UsuarioService:
    def __init__(self, repo: UsuarioRepository) -> None:
        self._repo = repo

    async def login(self, data: LoginRequest, ip: str | None = None) -> str:
        tentativas = await self._repo.count_tentativas_recentes(data.email)
        if tentativas >= MAX_TENTATIVAS:
            raise ContaBloqueadaError(
                f"Conta bloqueada após {MAX_TENTATIVAS} tentativas falhas. "
                "Tente novamente em 15 minutos."
            )

        usuario = await self._repo.get_by_email(data.email)
        senha_valida = usuario is not None and verify_password(data.senha, usuario.senha_hash)

        if not senha_valida:
            await self._repo.registrar_tentativa(data.email, sucesso=False, ip=ip)
            raise AuthError("E-mail ou senha inválidos.")

        assert usuario is not None  # narrowing for mypy

        if not usuario.ativo:
            raise AuthError("Usuário inativo. Contate o administrador.")

        await self._repo.registrar_tentativa(data.email, sucesso=True, ip=ip)

        jti = str(new_uuid())
        sessao = Sessao(
            usuario_id=usuario.id,
            token_jti=jti,
            expira_em=datetime.now(UTC) + timedelta(hours=SESSION_EXPIRE_HOURS),
            ip_origem=ip,
        )
        await self._repo.criar_sessao(sessao)
        usuario.ultimo_login_em = datetime.now(UTC)
        await self._repo.commit()

        token = create_access_token(
            str(usuario.id),
            extra={"jti": jti, "nome": usuario.nome, "tv": usuario.token_version},
        )
        logger.info("usuario_login", usuario_id=str(usuario.id), ip=ip)
        return token

    async def logout(self, jti: str) -> None:
        await self._repo.revogar_sessao(jti)
        await self._repo.commit()
        logger.info("usuario_logout", jti=jti)

    async def criar_usuario(
        self, data: UsuarioCreate, criado_por: uuid.UUID | None = None
    ) -> Usuario:
        existente = await self._repo.get_by_email(data.email)
        if existente is not None:
            raise ConflictError("Já existe um usuário com este e-mail.")

        usuario = Usuario(
            nome=data.nome,
            email=data.email.lower(),
            senha_hash=hash_password(data.senha),
            gestor=data.gestor,
        )
        await self._repo.create(usuario)
        await self._repo.commit()
        await self._repo.refresh(usuario)
        logger.info("usuario_criado", email=data.email, criado_por=str(criado_por))
        return usuario

    async def obter_usuario(self, usuario_id: uuid.UUID) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")
        return usuario

    async def atualizar_usuario(self, usuario_id: uuid.UUID, data: UsuarioUpdate) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(usuario, field, value)
        await self._repo.commit()
        await self._repo.refresh(usuario)
        return usuario

    async def alterar_senha(
        self, usuario_id: uuid.UUID, data: AlterarSenhaRequest
    ) -> None:
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        if not verify_password(data.senha_atual, usuario.senha_hash):
            raise AuthError("Senha atual incorreta.")

        usuario.senha_hash = hash_password(data.nova_senha)
        usuario.token_version += 1  # invalida todos os tokens já emitidos
        await self._repo.revogar_todas_sessoes_usuario(usuario_id)
        await self._repo.commit()
        logger.info("senha_alterada", usuario_id=str(usuario_id))

    async def recuperar_senha(self, email: str) -> None:
        usuario = await self._repo.get_by_email(email)
        if usuario is None:
            logger.info("recuperacao_senha_email_nao_encontrado", email=email)
            return

        token_raw = secrets.token_urlsafe(32)
        token_hash = UsuarioRepository.hash_token(token_raw)

        token = TokenSeguranca(
            usuario_id=usuario.id,
            tipo=TipoToken.RECUPERACAO_SENHA,
            token_hash=token_hash,
            expira_em=datetime.now(UTC) + timedelta(hours=TOKEN_RESET_EXPIRE_HOURS),
        )
        await self._repo.criar_token(token)
        await self._repo.commit()

        reset_url = f"http://localhost:4200/definir-senha/{token_raw}"
        html = (
            f"<p>Olá {usuario.nome},</p>"
            "<p>Recebemos uma solicitação para redefinir sua senha.</p>"
            f'<p><a href="{reset_url}">Clique aqui para definir sua nova senha</a></p>'
            f"<p>Este link expira em {TOKEN_RESET_EXPIRE_HOURS} horas.</p>"
            "<p>Se não foi você, ignore este e-mail.</p>"
        )
        try:
            smtp_sender.send(usuario.email, "Redefinição de senha — App Financeiro", html)
        except Exception:
            logger.exception("erro_envio_email_recuperacao_senha", email=email)

        logger.info("recuperacao_senha_solicitada", usuario_id=str(usuario.id))

    async def definir_senha(self, data: DefinirSenhaRequest) -> None:
        token_hash = UsuarioRepository.hash_token(data.token)
        token = await self._repo.get_token_by_hash(token_hash, TipoToken.RECUPERACAO_SENHA)

        if token is None or token.usado_em is not None:
            raise NotFoundError("Token inválido ou já utilizado.")

        expira_em = token.expira_em
        if expira_em.tzinfo is None:
            expira_em = expira_em.replace(tzinfo=UTC)
        if expira_em < datetime.now(UTC):
            raise DomainError("Token expirado. Solicite uma nova redefinição de senha.")

        usuario = await self._repo.get_by_id(token.usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")

        usuario.senha_hash = hash_password(data.nova_senha)
        usuario.token_version += 1  # invalida todos os tokens já emitidos
        token.usado_em = datetime.now(UTC)
        await self._repo.revogar_todas_sessoes_usuario(usuario.id)
        await self._repo.commit()
        logger.info("senha_redefinida", usuario_id=str(usuario.id))

    async def listar_usuarios(self) -> list[Usuario]:
        return list(await self._repo.list_all())

    async def inativar_usuario(self, usuario_id: uuid.UUID, admin_id: uuid.UUID) -> Usuario:
        if usuario_id == admin_id:
            raise DomainError("Você não pode inativar sua própria conta.")
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")
        if not usuario.ativo:
            raise DomainError("Usuário já está inativo.")
        usuario.ativo = False
        usuario.token_version += 1  # derruba a sessão do usuário imediatamente
        await self._repo.revogar_todas_sessoes_usuario(usuario_id)
        await self._repo.commit()
        await self._repo.refresh(usuario)
        return usuario

    async def reativar_usuario(self, usuario_id: uuid.UUID) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")
        if usuario.ativo:
            raise DomainError("Usuário já está ativo.")
        usuario.ativo = True
        await self._repo.commit()
        await self._repo.refresh(usuario)
        return usuario

    async def toggle_gestor(self, usuario_id: uuid.UUID, admin_id: uuid.UUID) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado.")
        if usuario.admin:
            raise DomainError("Administradores não podem ser rebaixados a gestor por esta operação.")
        if usuario_id == admin_id:
            raise DomainError("Você não pode alterar seu próprio perfil.")
        usuario.gestor = not usuario.gestor
        await self._repo.commit()
        await self._repo.refresh(usuario)
        logger.info("usuario_gestor_alterado", usuario_id=str(usuario_id), gestor=usuario.gestor)
        return usuario
