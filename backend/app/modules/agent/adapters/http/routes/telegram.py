"""Webhook do Telegram.

Valida o `secret_path` do caminho (e o header `X-Telegram-Bot-Api-Secret-Token`
quando presente), responde `200` **imediatamente** e processa o update em
background. O Telegram reentrega updates não respondidos em poucos segundos, e um
turno com várias tool calls passa disso — a resposta HTTP não pode esperar o
turno terminar.
"""

import asyncio
import hmac
import logging
from collections.abc import Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.modules.agent.adapters.http.dependencies import ContainerDep
from app.modules.agent.container import Container

logger = logging.getLogger(__name__)

router = APIRouter()

_SECRET_HEADER = "x-telegram-bot-api-secret-token"


@router.post("/webhook/telegram/{secret_path}")
async def telegram_webhook(
    secret_path: str,
    request: Request,
    container: ContainerDep,
) -> dict[str, bool]:
    """Recebe um update, valida o segredo e agenda o processamento."""
    _verify_secret(secret_path, request, container)
    payload: dict[str, Any] = await request.json()
    _process_in_background(request, container.handle_update(payload))
    return {"ok": True}


def _verify_secret(secret_path: str, request: Request, container: Container) -> None:
    """`404` (não `403`) quando o segredo não bate: um `403` confirmaria a rota."""
    if not hmac.compare_digest(secret_path, container.webhook_secret):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    header = request.headers.get(_SECRET_HEADER)
    if header is not None and not hmac.compare_digest(header, container.webhook_secret):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _process_in_background(request: Request, coro: Coroutine[Any, Any, None]) -> None:
    """Agenda a coroutine e a segura num set do `app` para o GC não a coletar."""
    tasks: set[asyncio.Task[None]] = request.app.state.background_tasks
    task = asyncio.create_task(coro)
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    task.add_done_callback(_log_background_failure)


def _log_background_failure(task: asyncio.Task[None]) -> None:
    """Registra (sem re-levantar) uma falha que tenha escapado do processamento."""
    if not task.cancelled() and task.exception() is not None:
        logger.error("Processamento de update falhou", exc_info=task.exception())
