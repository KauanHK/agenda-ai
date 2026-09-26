"""Entrypoint do uvicorn: `uv run uvicorn app.main_agent:app`.

Lê a configuração uma vez, ajusta o logging e monta a aplicação. Um erro de
configuração aqui derruba o boot, que é onde ele deve aparecer.
"""

from app.modules.agent.adapters.http.app import create_app
from app.modules.agent.logging_config import configure_logging
from app.modules.agent.settings import Settings

settings = Settings()  # pyright: ignore[reportCallIssue]

configure_logging(settings.observability.log_level)

app = create_app(settings)
