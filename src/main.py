"""Entrypoint do uvicorn: `uv run uvicorn src.main:app`.

Lê a configuração uma vez, ajusta o logging e monta a aplicação. Um erro de
configuração aqui derruba o boot, que é onde ele deve aparecer.
"""

from src.interfaces.http.app import create_app
from src.logging_config import configure_logging
from src.settings import Settings

settings = Settings()  # pyright: ignore[reportCallIssue]

# Cobre o que loga antes da app existir; `create_app` chama de novo (idempotente,
# `force=True`) para pegar o `TestClient` e o `uvicorn --reload`.
configure_logging(settings.observability.log_level)

app = create_app(settings)
