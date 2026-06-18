from contextlib import asynccontextmanager
import os
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.chat_ws import router as chat_ws_router
from app.routers.conversations import router as conversations_router
from app.routers.upload import router as upload_router
from app.core.config import settings
from app.db.base import Base, engine
from app.models import (
    conversation,
    message,
)  # noqa: F401 — registra modelos no metadata
from app.observability.noop import NoOpTracer
from app.services.ai_service import AIService


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.dev.ConsoleRenderer()
                if settings.APP_DEBUG
                else structlog.processors.JSONRenderer()
            ),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )


def _build_ai_service() -> AIService:
    """
    Instancia o provider correto com base em AI_PROVIDER no .env.
    Trocar provider não requer mudança nesta função — apenas a variável de ambiente.
    """
    tracer = NoOpTracer()

    if settings.AI_PROVIDER == "claude":
        from app.providers.claude import ClaudeProvider

        provider = ClaudeProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.CLAUDE_MODEL,
        )
    elif settings.AI_PROVIDER == "gemini":
        from app.providers.gemini import GeminiProvider

        provider = GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )
    else:
        from app.providers.mock import MockProvider

        provider = MockProvider()

    return AIService(provider=provider, tracer=tracer)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    Path("uploads").mkdir(exist_ok=True)
    app.state.ai_service = _build_ai_service()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await engine.dispose()


app = FastAPI(
    title="Assistente de Marca",
    description="API do assistente de marca para franqueados",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_ws_router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations_router, prefix=settings.API_V1_PREFIX)
app.include_router(upload_router, prefix=settings.API_V1_PREFIX)

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
