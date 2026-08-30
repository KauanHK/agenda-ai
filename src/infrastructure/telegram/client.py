"""Envio de respostas e do indicador de "digitando" pela Bot API do Telegram.

Nenhuma dependência do `python-telegram-bot`: a Bot API é REST simples e o que
o agente precisa são duas chamadas (`sendMessage` e `sendChatAction`) sobre
`httpx`. O envio é sem `parse_mode` (ver `formatting.py`).
"""

import asyncio
import logging
from typing import Any

import httpx

from src.domain.entities import Contact
from src.domain.exceptions import DeliveryError
from src.infrastructure.telegram.formatting import split_for_telegram, to_telegram_text

logger = logging.getLogger(__name__)

_DEFAULT_RETRY_AFTER_SECONDS = 1.0


def build_telegram_client(
    *,
    api_root: str,
    bot_token: str,
    timeout_seconds: float,
) -> httpx.AsyncClient:
    """Cria o `AsyncClient` da Bot API com o token embutido na `base_url`.

    `api_root` vem da configuração (`TELEGRAM__API_ROOT`, padrão
    `https://api.telegram.org`) para permitir apontar o bot a um Local Bot API
    Server ou a um endpoint de teste/staging.

    O token vai na URL porque a Bot API exige (`/bot<token>/<método>`); como o
    `X-Service-Key` do AgendaBot, ele vive só dentro deste pacote e nunca entra
    em log nem em mensagem de erro.
    """
    return httpx.AsyncClient(
        base_url=f"{api_root}/bot{bot_token}",
        timeout=httpx.Timeout(timeout_seconds),
    )


class TelegramMessenger:
    """Implementa `OutboundMessengerProtocol` sobre a Bot API."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send_text(self, contact: Contact, text: str) -> None:
        """Normaliza o texto, quebra no teto de 4096 e envia pedaço a pedaço."""
        for chunk in split_for_telegram(to_telegram_text(text)):
            await self._send_message(contact.channel_user_id, chunk)

    async def signal_typing(self, contact: Contact) -> None:
        """Chama `sendChatAction` e engole qualquer falha."""
        try:
            await self._client.post(
                "/sendChatAction",
                json={"chat_id": contact.channel_user_id, "action": "typing"},
            )
        except httpx.HTTPError as exc:
            logger.debug("sendChatAction falhou (%s); seguindo sem o indicador", type(exc).__name__)

    async def _send_message(self, chat_id: str, text: str, *, allow_retry: bool = True) -> None:
        """Envia um pedaço; num `429` respeita o `retry_after` e tenta uma vez."""
        response = await self._post_message(chat_id, text)
        if response.status_code == httpx.codes.TOO_MANY_REQUESTS and allow_retry:
            await asyncio.sleep(_retry_after(response))
            await self._send_message(chat_id, text, allow_retry=False)
            return
        if response.is_error:
            raise DeliveryError(f"O Telegram recusou o envio (HTTP {response.status_code}).")

    async def _post_message(self, chat_id: str, text: str) -> httpx.Response:
        """Faz o `POST /sendMessage`, traduzindo falha de transporte em `DeliveryError`."""
        try:
            return await self._client.post("/sendMessage", json={"chat_id": chat_id, "text": text})
        except httpx.HTTPError as exc:
            # `from None`: o `__cause__` de um erro do httpx carrega a URL com o
            # token do bot, e este erro pode ser logado com o stacktrace inteiro.
            logger.warning("Falha de transporte ao enviar ao Telegram: %s", type(exc).__name__)
            raise DeliveryError("Falha de transporte ao falar com o Telegram.") from None


def _retry_after(response: httpx.Response) -> float:
    """Lê `parameters.retry_after` do corpo do `429`, ou usa o default."""
    try:
        body: dict[str, Any] = response.json()
    except ValueError:
        return _DEFAULT_RETRY_AFTER_SECONDS
    parameters = body.get("parameters")
    if isinstance(parameters, dict):
        retry_after = parameters.get("retry_after")
        if isinstance(retry_after, (int, float)) and retry_after >= 0:
            return float(retry_after)
    return _DEFAULT_RETRY_AFTER_SECONDS
