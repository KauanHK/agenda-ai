from typing import Any, Protocol

from app.modules.channels.domain.entities import BotIdentity


class TelegramBotApiProtocol(Protocol):
    """Chamadas de administração do bot; o token vai por chamada (um SaaS, vários bots)."""

    async def get_me(self, bot_token: str) -> BotIdentity: ...

    async def set_webhook(
        self,
        bot_token: str,
        *,
        url: str,
        secret_token: str,
        drop_pending_updates: bool = False,
    ) -> None: ...

    async def delete_webhook(
        self, bot_token: str, *, drop_pending_updates: bool
    ) -> None: ...

    async def get_webhook_info(self, bot_token: str) -> dict[str, Any]: ...
