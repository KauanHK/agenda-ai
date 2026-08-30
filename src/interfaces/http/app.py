"""Fábrica da aplicação FastAPI.

O lifespan monta o `Container` (uma vez) e o guarda em `app.state`; as rotas o
consomem via a dependência `get_container`. O `AsyncExitStack` do container é
fechado no shutdown.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.container import build_container
from src.interfaces.http.routes import health, telegram
from src.settings import Settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Monta a aplicação. Sem `settings`, carrega a configuração do ambiente."""
    resolved_settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container, stack = await build_container(resolved_settings)
        app.state.container = container
        app.state.background_tasks = set()
        logger.info("Aplicação pronta")
        async with stack:
            yield

    app = FastAPI(title="agente-agenda", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(telegram.router)
    return app
