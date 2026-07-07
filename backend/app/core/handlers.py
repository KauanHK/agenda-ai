from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registra os manipuladores de exceção personalizados na aplicação FastAPI.

    Args:
        app (FastAPI):
            A instância do FastAPI onde os manipuladores de exceção serão registrados.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )
