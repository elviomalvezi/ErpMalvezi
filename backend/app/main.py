from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import settings
from app.modules.categoria.routes import router as categoria_router
from app.modules.patrimonio.routes import router as patrimonio_router
from app.modules.conciliacao.routes import router as conciliacao_router
from app.modules.conta_bancaria.routes import router as conta_bancaria_router
from app.modules.contato.routes import router as contato_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.empresa.routes import router as empresa_router
from app.modules.fatura.routes import router as fatura_router
from app.modules.fluxo_caixa.routes import router as fluxo_caixa_router
from app.modules.lancamento.routes import router as lancamento_router
from app.modules.permissao.routes import router as permissao_router
from app.modules.transferencia.routes import router as transferencia_router
from app.modules.usuario.routes import router_auth, router_usuarios

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("backend_started", environment=settings.environment)
    yield


app = FastAPI(
    title="App Financeiro",
    description="Plataforma web de controle financeiro",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(router_auth, prefix="/api/v1")
app.include_router(router_usuarios, prefix="/api/v1")
app.include_router(empresa_router, prefix="/api/v1")
app.include_router(permissao_router, prefix="/api/v1")
app.include_router(categoria_router, prefix="/api/v1")
app.include_router(contato_router, prefix="/api/v1")
app.include_router(conta_bancaria_router, prefix="/api/v1")
app.include_router(fatura_router, prefix="/api/v1")
app.include_router(lancamento_router, prefix="/api/v1")
app.include_router(transferencia_router, prefix="/api/v1")
app.include_router(conciliacao_router, prefix="/api/v1")
app.include_router(fluxo_caixa_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(patrimonio_router, prefix="/api/v1")
