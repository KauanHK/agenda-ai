from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.handlers import register_exception_handlers
from app.core.middleware import setup_middleware
from app.db.session import db


def mount_routes(app: FastAPI) -> None:
    """
    Registra os roteadores da aplicação.

    Args:
        app (FastAPI):
            A instância da aplicação FastAPI onde
            os routers serão registrados.
    """

    app.include_router(api_router)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """
    Gerencia o ciclo de vida da aplicação, garantindo que o
    banco de dados seja inicializado e fechado corretamente.
    """

    db.init()
    yield
    await db.close()


def create_app() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI, registrando os manipuladores
    de exceção e middlewares necessários.

    Returns:
        FastAPI: A instância configurada da aplicação FastAPI.
    """

    app = FastAPI(
        title="AgendaBot API",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    setup_middleware(app)
    mount_routes(app)

    return app
