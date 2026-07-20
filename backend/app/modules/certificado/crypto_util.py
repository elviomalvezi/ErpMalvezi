"""Cifragem simétrica da senha do certificado (em repouso).

Usa Fernet com uma chave derivada do SECRET_KEY da aplicação. A senha nunca é
gravada em texto puro; só é decifrada sob demanda para download/uso.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    chave = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
    return Fernet(chave)


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode()).decode()


def decifrar(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
