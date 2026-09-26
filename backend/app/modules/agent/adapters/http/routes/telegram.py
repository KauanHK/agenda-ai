"""Webhook do Telegram, um por estabelecimento.

O `establishment_id` do caminho escolhe o bot; o header
`X-Telegram-Bot-Api-Secret-Token` com o segredo daquele bot autentica o update. A rota
responde `200` **imediatamente** e processa o update em background: o Telegram
reentrega updates não respondidos em poucos segundos, e um turno com várias tool
calls passa disso — a resposta HTTP não pode esperar o turno terminar.

Toda rejeição é `404`, nunca `401`/`403`: um `403` confirmaria que a rota existe para
aquele id. A exceção é o banco fora (`503`), para o Telegram reenviar depois.
"""

import asyncio
import hmac
import logging
import uuid
from collections.abc import Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.modules.agent.adapters.http.dependencies import ContainerDep
from app.modules.agent.container import Container
from app.modules.agent.domain.entities import TelegramChannel
from app.modules.agent.domain.exceptions import ChannelLookupError

logger = logging.getLogger(__name__)

router = APIRouter()

_SECRET_HEADER = "x-telegram-bot-api-secret-token"


@router.post("/webhook/telegram/{establishment_id}")
async def telegram_webhook(
    establishment_id: str,
    request: Request,
    container: ContainerDep,
) -> dict[str, bool]:
    """Recebe um update, autentica pelo bot do estabelecimento e agenda o processamento.

    O id chega como `str` e é convertido à mão: um `uuid.UUID` no caminho faria o
    FastAPI responder `422`.
    """
    channel = await _authenticate(establishment_id, request, container)
    payload: dict[str, Any] = await request.json()
    _process_in_background(
        request, container.handle_update(channel.establishment, payload)
    )
    return {"ok": True}


async def _authenticate(
    establishment_id: str, request: Request, container: Container
) -> TelegramChannel:
    """Devolve o canal do estabelecimento se o header traz o segredo do bot dele."""
    try:
        parsed_id = uuid.UUID(establishment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from None
    try:
        channel = await container.channels.get(parsed_id)
    except ChannelLookupError:
        logger.warning("Diretório de canais indisponível; o Telegram vai reenviar")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None
    header = request.headers.get(_SECRET_HEADER)
    if (
        channel is None
        or header is None
        # Em bytes: `compare_digest` recusa `str` com caractere fora do ASCII.
        or not hmac.compare_digest(header.encode(), channel.webhook_secret.encode())
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return channel


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
