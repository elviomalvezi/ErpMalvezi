import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import settings
from app.modules.busca.routes import router as busca_router
from app.modules.categoria.routes import router as categoria_router
from app.modules.certificado.routes import router as certificado_router
from app.modules.patrimonio.routes import router as patrimonio_router
from app.modules.conciliacao.routes import router as conciliacao_router
from app.modules.conta_bancaria.routes import router as conta_bancaria_router
from app.modules.contato.routes import router as contato_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.empresa.routes import router as empresa_router
from app.modules.fatura.routes import router as fatura_router
from app.modules.fluxo_caixa.routes import router as fluxo_caixa_router
from app.modules.lancamento.routes import router as lancamento_router
from app.modules.notificacao.routes import router as notificacao_router
from app.modules.pessoa.routes import router as pessoa_router
from app.modules.pessoa.routes import router_certificado as pessoa_certificado_router
from app.modules.permissao.routes import router as permissao_router
from app.modules.relatorio.routes import router as relatorio_router
from app.modules.transferencia.routes import router as transferencia_router
from app.modules.auditoria.routes import router as auditoria_router
from app.modules.usuario.routes import router_auth, router_usuarios

logger = structlog.get_logger()


async def _job_notificacoes_diarias() -> None:
    """Job que roda diariamente às 8h enviando alertas de vencimento por e-mail."""
    from app.core.database import AsyncSessionLocal
    from app.modules.notificacao.service import NotificacaoService

    while True:
        now = datetime.now()
        proxima = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= proxima:
            proxima += timedelta(days=1)
        await asyncio.sleep((proxima - now).total_seconds())
        try:
            async with AsyncSessionLocal() as db:
                await NotificacaoService(db).enviar_vencimentos()
        except Exception:
            logger.exception("erro_job_notificacoes_diarias")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    task = asyncio.create_task(_job_notificacoes_diarias())
    logger.info("backend_started", environment=settings.environment)
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


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


from fastapi import Request  # noqa: E402
from fastapi.encoders import jsonable_encoder  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # jsonable_encoder garante que valores não-serializáveis no contexto do erro
    # (Decimal de constraints como gt/ge, date, etc.) não quebrem a resposta 422.
    # Remove o campo `input` (valor enviado pelo cliente) para não vazar senha/PII
    # nos logs nem refleti-lo de volta na resposta.
    detail = [
        {k: v for k, v in erro.items() if k != "input"}
        for erro in jsonable_encoder(exc.errors())
    ]
    logger.error("validation_error", url=str(request.url), errors=detail)
    return JSONResponse(status_code=422, content={"detail": detail})

app.include_router(health_router, prefix="/api/v1")
app.include_router(router_auth, prefix="/api/v1")
app.include_router(router_usuarios, prefix="/api/v1")
app.include_router(empresa_router, prefix="/api/v1")
app.include_router(permissao_router, prefix="/api/v1")
app.include_router(categoria_router, prefix="/api/v1")
app.include_router(certificado_router, prefix="/api/v1")
app.include_router(pessoa_router, prefix="/api/v1")
app.include_router(pessoa_certificado_router, prefix="/api/v1")
app.include_router(contato_router, prefix="/api/v1")
app.include_router(conta_bancaria_router, prefix="/api/v1")
app.include_router(fatura_router, prefix="/api/v1")
app.include_router(lancamento_router, prefix="/api/v1")
app.include_router(transferencia_router, prefix="/api/v1")
app.include_router(conciliacao_router, prefix="/api/v1")
app.include_router(fluxo_caixa_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(patrimonio_router, prefix="/api/v1")
app.include_router(auditoria_router, prefix="/api/v1")
app.include_router(notificacao_router, prefix="/api/v1")
app.include_router(relatorio_router, prefix="/api/v1")
app.include_router(busca_router, prefix="/api/v1")
