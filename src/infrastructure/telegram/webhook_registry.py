"""Registro e consulta do webhook do bot na Bot API (`setWebhook` / `getWebhookInfo`).

É operação administrativa, feita uma vez por ambiente (o Telegram guarda a URL
do lado dele): não entra no turno da conversa e por isso não é uma porta da
aplicação — o `Container` só expõe as duas chamadas para a rota `/admin`.

Reutiliza o `httpx.AsyncClient` de `client.py`, que já carrega o token na
`base_url`. O segredo do webhook faz parte da URL registrada e volta no
`getWebhookInfo`; o que sai daqui já vem com ele mascarado.
"""

import logging
from typing import Any

import httpx

from src.domain.exceptions import WebhookRegistrationError

logger = logging.getLogger(__name__)

WEBHOOK_PATH_TEMPLATE = "/webhook/telegram/{secret}"
_REDACTED = "***"
_ALLOWED_UPDATES = ["message"]


class TelegramWebhookRegistry:
    """Registra e consulta o webhook do bot; devolve o `getWebhookInfo` mascarado."""

    def __init__(self, client: httpx.AsyncClient, *, webhook_secret: str) -> None:
        self._client = client
        self._webhook_secret = webhook_secret

    def webhook_url(self, base_url: str) -> str:
        """URL completa do webhook a partir da base pública (sem barra final)."""
        return base_url.rstrip("/") + WEBHOOK_PATH_TEMPLATE.format(secret=self._webhook_secret)

    async def register(
        self, base_url: str, *, drop_pending_updates: bool = False
    ) -> dict[str, Any]:
        """`setWebhook` apontando para `base_url`; devolve o `getWebhookInfo` resultante.

        Só updates do tipo `message` são pedidos — é o que o parser entende — e o
        segredo vai também em `secret_token`, que a rota valida no header.

        Raises:
            WebhookRegistrationError: Se o Telegram recusar ou não responder.
        """
        payload = {
            "url": self.webhook_url(base_url),
            "secret_token": self._webhook_secret,
            "allowed_updates": _ALLOWED_UPDATES,
            "drop_pending_updates": drop_pending_updates,
        }
        await self._call("setWebhook", json=payload)
        logger.info("Webhook do Telegram registrado em %s", self._redact(base_url))
        return await self.info()

    async def info(self) -> dict[str, Any]:
        """`getWebhookInfo` com o segredo mascarado na `url`."""
        result = await self._call("getWebhookInfo")
        if isinstance(result.get("url"), str):
            result["url"] = self._redact(result["url"])
        return result

    async def _call(self, method: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Chama um método da Bot API e devolve o campo `result`.

        `from None`: o `__cause__` de um erro do httpx carrega a URL com o token
        do bot, e este erro pode ser logado com o stacktrace inteiro.
        """
        try:
            response = await self._client.post(f"/{method}", json=json)
        except httpx.HTTPError as exc:
            logger.warning("Falha de transporte no %s: %s", method, type(exc).__name__)
            raise WebhookRegistrationError("Falha de transporte ao falar com o Telegram.") from None

        body = self._parse_body(method, response)
        if response.is_error or not body.get("ok"):
            description = body.get("description") or f"HTTP {response.status_code}"
            raise WebhookRegistrationError(
                f"O Telegram recusou o {method}: {self._redact(str(description))}"
            )
        result = body.get("result")
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _parse_body(method: str, response: httpx.Response) -> dict[str, Any]:
        try:
            body: Any = response.json()
        except ValueError:
            raise WebhookRegistrationError(
                f"O Telegram respondeu ao {method} sem JSON (HTTP {response.status_code})."
            ) from None
        return body if isinstance(body, dict) else {}

    def _redact(self, text: str) -> str:
        return text.replace(self._webhook_secret, _REDACTED)
