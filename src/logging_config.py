"""Logging estruturado: uma linha JSON por registro, no stdout.

Sem dependência nova — um `logging.Formatter` próprio serializa cada record. O
`thread_id` do turno viaja num `ContextVar` e é injetado em todo registro por um
`logging.Filter`; quem abre o turno (o handler do webhook) o amarra com
`bind_thread_id` e o solta no `finally`.

Regra de privacidade: o telefone sintético e o `session_token` **nunca** entram
num log. Hoje nenhum `logger.*` os passa — ao logar algo novo, não inclua o
`Contact.phone`, o `BookingSession.token` nem o `session_token` do AgendaBot.
"""

import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

_thread_id_var: ContextVar[str | None] = ContextVar("thread_id", default=None)

# Atributos que o `logging` já põe no record e que o formatter trata à parte (ou
# ignora). Tudo que sobra em `record.__dict__` veio de um `extra=` e entra no JSON.
_RESERVED_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "message",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
        "thread_id",
    }
)


@contextmanager
def bind_thread_id(thread_id: str) -> Generator[None]:
    """Amarra o `thread_id` ao contexto do turno; solta ao sair do bloco."""
    token = _thread_id_var.set(thread_id)
    try:
        yield
    finally:
        _thread_id_var.reset(token)


class _ThreadIdFilter(logging.Filter):
    """Copia o `thread_id` do `ContextVar` para cada record que passa pelo handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "thread_id"):
            record.thread_id = _thread_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Serializa o record numa única linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        thread_id = getattr(record, "thread_id", None)
        if thread_id is not None:
            payload["thread_id"] = thread_id

        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str) -> None:
    """Manda todo o `logging` para o stdout em JSON, no nível dado.

    `force=True`: idempotente e sobrepõe qualquer handler anterior (o do
    `uvicorn --reload`, o de um `configure_logging` anterior num teste).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(_ThreadIdFilter())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
