from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do projeto (AppFinanceiro/) independente do CWD
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Valores de placeholder dos arquivos .env*.example — nunca podem chegar a produção.
_SECRET_KEY_PLACEHOLDERS = {
    "troque-esta-chave-em-producao-use-openssl-rand-hex-32",
    "GERE_UMA_CHAVE_SECRETA_AQUI",
    "changeme",
    "secret",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_PROJECT_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Fail-safe: se ENVIRONMENT não estiver setado, assume produção (sem /docs,
    # sem echo SQL, CORS restrito). Dev deve declarar ENVIRONMENT=development.
    environment: str = "production"
    secret_key: str
    database_url: str

    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin123"
    storage_bucket: str = "appfinanceiro"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@appfinanceiro.local"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL deve usar driver postgresql")
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        # Em produção a SECRET_KEY não pode ser placeholder nem curta demais —
        # caso contrário JWTs podem ser forjados. Falha no boot.
        if not self.is_development:
            if self.secret_key in _SECRET_KEY_PLACEHOLDERS:
                raise ValueError(
                    "SECRET_KEY está com valor placeholder. Gere uma chave forte "
                    "(ex.: `openssl rand -hex 32`) antes de subir em produção."
                )
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY deve ter ao menos 32 caracteres em produção.")
        return self


settings = Settings()  # type: ignore[call-arg]
