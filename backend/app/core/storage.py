"""Adapter de armazenamento de arquivos.

Implementações:
- LocalStorageProvider: salva em disco local (dev e VM interna sem MinIO)
- S3StorageProvider: MinIO / AWS S3 compatível (via boto3 — adicionar ao pyproject quando necessário)

A interface StorageProvider permite trocar o backend sem alterar código de domínio.
"""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    @abstractmethod
    async def salvar(self, conteudo: bytes, caminho: str, content_type: str) -> str:
        """Salva `conteudo` no caminho relativo informado e retorna a URL/path pública."""

    @abstractmethod
    async def ler(self, caminho: str) -> bytes:
        """Lê o conteúdo do arquivo no caminho relativo informado."""

    @abstractmethod
    async def excluir(self, caminho: str) -> None:
        """Remove o arquivo do caminho relativo informado."""


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | Path, base_url: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    async def salvar(self, conteudo: bytes, caminho: str, content_type: str) -> str:
        destino = self._base_dir / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return f"{self._base_url}/{caminho}"

    async def ler(self, caminho: str) -> bytes:
        destino = self._base_dir / caminho
        if not destino.exists():
            raise FileNotFoundError(caminho)
        return destino.read_bytes()

    async def excluir(self, caminho: str) -> None:
        destino = self._base_dir / caminho
        if destino.exists():
            destino.unlink()


def gerar_caminho_logo(empresa_id: uuid.UUID, extensao: str) -> str:
    return f"logos/{empresa_id}.{extensao.lstrip('.')}"


def get_storage_provider() -> StorageProvider:
    base_dir = os.environ.get("STORAGE_LOCAL_PATH", "media")
    base_url = os.environ.get("STORAGE_LOCAL_URL", "http://localhost:8000/media")
    return LocalStorageProvider(base_dir, base_url)
