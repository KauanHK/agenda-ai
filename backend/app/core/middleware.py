from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI) -> None:
    """
    Configura os middlewares da aplicação.

    Args:
        app (FastAPI): A instância do FastAPI onde os middlewares serão registrados.
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
