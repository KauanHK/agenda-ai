"""Entrypoint do uvicorn: `uv run uvicorn src.main:app`.

Lê a configuração uma vez, ajusta o logging e monta a aplicação. Um erro de
configuração aqui derruba o boot, que é onde ele deve aparecer.
"""

import logging

from src.interfaces.http.app import create_app
from src.settings import Settings

settings = Settings()  # pyright: ignore[reportCallIssue]

logging.basicConfig(
    level=settings.observability.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = create_app(settings)
