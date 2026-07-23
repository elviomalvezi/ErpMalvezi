"""Cria o primeiro usuário administrador da plataforma.

Uso:
    uv run python scripts/criar_admin.py <email> <nome> <senha>
    uv run python scripts/criar_admin.py  (interativo)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.modules.usuario.models import Usuario


async def main(email: str, nome: str, senha: str) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        existente = await session.scalar(select(Usuario).where(Usuario.email == email))
        if existente:
            print(f"[aviso] Usuário {email} já existe. Nada foi alterado.")
            await engine.dispose()
            return

        admin = Usuario(
            email=email,
            nome=nome,
            senha_hash=hash_password(senha),
            ativo=True,
            admin=True,
            email_verificado=True,
        )
        session.add(admin)
        await session.commit()
        print("[ok] Administrador criado com sucesso.")
        print(f"     E-mail : {email}")
        print(f"     Nome   : {nome}")

    await engine.dispose()


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 3:
        _email, _nome, _senha = args[0], args[1], args[2]
    else:
        _email = input("E-mail: ").strip()
        _nome = input("Nome  : ").strip()
        _senha = input("Senha : ").strip()

    asyncio.run(main(_email, _nome, _senha))
