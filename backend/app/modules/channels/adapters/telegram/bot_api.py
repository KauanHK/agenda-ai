"""Cliente das chamadas de administração do bot na Bot API do Telegram.

O token vai **por chamada** (`/bot{token}/{método}`), porque o SaaS fala com o bot de
cada estabelecimento; o `httpx.AsyncClient` só conhece a raiz da Bot API.

Nada sensível sai daqui: os erros são levantados com `from None` (o `__cause__` do
httpx carrega a URL com o token), a `description` do Telegram volta com o token e o
segredo trocados por `***`.
"""

import logging
from typing import Any

import httpx

from app.modules.channels.domain.entities import BotIdentity
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)

logger = logging.getLogger(__name__)

TELEGRAM_API_ROOT = "https://api.telegram.org"
_CONNECT_TIMEOUT_SECONDS = 5.0
_READ_TIMEOUT_SECONDS = 10.0
_REDACTED = "***"
# É o que o parser do agente entende.
_ALLOWED_UPDATES = ["message"]
_INVALID_TOKEN_STATUSES = (httpx.codes.UNAUTHORIZED, httpx.codes.NOT_FOUND)


def build_bot_api_client(api_root: str = TELEGRAM_API_ROOT) -> httpx.AsyncClient:
    """`AsyncClient` na raiz da Bot API, sem token.

    Timeouts curtos: a Bot API responde rápido ou não responde. `api_root` existe para
    apontar a um Local Bot API Server ou a um endpoint de teste.
    """
    return httpx.AsyncClient(
        base_url=api_root,
        timeout=httpx.Timeout(_READ_TIMEOUT_SECONDS, connect=_CONNECT_TIMEOUT_SECONDS),
    )


class TelegramBotApi:
    """Implementa `TelegramBotApiProtocol` sobre `httpx`."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_me(self, bot_token: str) -> BotIdentity:
        result = await self._call(bot_token, "getMe")
        bot_id, username = result.get("id"), result.get("username")
        if not isinstance(bot_id, int) or not isinstance(username, str):
            raise TelegramApiError("O Telegram respondeu ao getMe sem id ou username.")
        return BotIdentity(id=bot_id, username=username)

    async def set_webhook(
        self,
        bot_token: str,
        *,
        url: str,
        secret_token: str,
        drop_pending_updates: bool = False,
    ) -> None:
        payload = {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": _ALLOWED_UPDATES,
            "drop_pending_updates": drop_pending_updates,
        }
        await self._call(bot_token, "setWebhook", json=payload, secrets=(secret_token,))
        logger.info(
            "Webhook do Telegram registrado em %s", url.replace(secret_token, _REDACTED)
        )

    async def delete_webhook(
        self, bot_token: str, *, drop_pending_updates: bool
    ) -> None:
        await self._call(
            bot_token,
            "deleteWebhook",
            json={"drop_pending_updates": drop_pending_updates},
        )

    async def _call(
        self,
        bot_token: str,
        method: str,
        *,
        json: dict[str, Any] | None = None,
        secrets: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        """Chama um método da Bot API e devolve o campo `result` (vazio se não for objeto)."""
        try:
            response = await self._client.post(f"/bot{bot_token}/{method}", json=json)
        except httpx.HTTPError as exc:
            logger.warning("Falha de transporte no %s: %s", method, type(exc).__name__)
            raise TelegramApiError(
                "Falha de transporte ao falar com o Telegram."
            ) from None

        if response.status_code in _INVALID_TOKEN_STATUSES:
            raise InvalidBotTokenError(
                f"O Telegram recusou o token do bot no {method}."
            )
        body = _parse_body(method, response)
        if response.is_error or not body.get("ok"):
            description = str(body.get("description") or f"HTTP {response.status_code}")
            for secret in filter(None, (bot_token, *secrets)):
                description = description.replace(secret, _REDACTED)
            raise TelegramApiError(f"O Telegram recusou o {method}: {description}")
        result = body.get("result")
        return result if isinstance(result, dict) else {}


def _parse_body(method: str, response: httpx.Response) -> dict[str, Any]:
    try:
        body: Any = response.json()
    except ValueError:
        raise TelegramApiError(
            f"O Telegram respondeu ao {method} sem JSON (HTTP {response.status_code})."
        ) from None
    return body if isinstance(body, dict) else {}
