import re
from datetime import datetime
from typing import Any, Self

from pydantic import SecretStr, field_validator, model_validator

from app.core.schemas import BaseSchema
from app.modules.channels.domain.entities import TelegramBot

_BOT_TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")


class TelegramChannelConnect(BaseSchema):
    bot_token: SecretStr

    @model_validator(mode="before")
    @classmethod
    def _wrap_bot_token(cls, data: Any) -> Any:
        # O erro de validação ecoa o `input` no corpo do `422`. Embrulhado antes, o
        # token volta como `**********`, e não em claro.
        if isinstance(data, dict) and isinstance(data.get("bot_token"), str):
            data = {**data, "bot_token": SecretStr(data["bot_token"])}
        return data

    @field_validator("bot_token")
    @classmethod
    def _validate_bot_token(cls, value: SecretStr) -> SecretStr:
        if not _BOT_TOKEN_PATTERN.match(value.get_secret_value()):
            raise ValueError("Formato de token do bot inválido.")
        return value


class TelegramChannelRead(BaseSchema):
    """Status do bot. Nunca carrega o token nem o segredo do webhook."""

    connected: bool
    bot_id: int | None
    bot_username: str | None
    connected_at: datetime | None

    @classmethod
    def from_bot(cls, bot: TelegramBot | None) -> Self:
        if bot is None:
            return cls(
                connected=False, bot_id=None, bot_username=None, connected_at=None
            )
        return cls(
            connected=True,
            bot_id=bot.bot_id,
            bot_username=bot.bot_username,
            # Toda conexão regrava a linha, então `updated_at` é a da última.
            connected_at=bot.updated_at,
        )
