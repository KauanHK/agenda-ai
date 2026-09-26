import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

from app.core.actors.user import Membership, UserActor
from app.modules.channels.domain.entities import BotIdentity, TelegramBot

TOKEN = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
OTHER_TOKEN = "987654321:BBHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
BASE_URL = "https://agenda.example.com"


class FakeChannelsUnitOfWork:
    """Fake de `ChannelsUnitOfWorkProtocol` que registra commit e rollback."""

    def __init__(self) -> None:
        self.telegram_bots = AsyncMock()
        self.establishments = AsyncMock()
        self.telegram_bots.get_by_bot_id.return_value = None
        self.telegram_bots.get_by_establishment.return_value = None
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.committed = exc_type is None


def make_bot_api(bot_id: int = 123456789, username: str = "barbearia_bot") -> AsyncMock:
    bot_api = AsyncMock()
    bot_api.get_me.return_value = BotIdentity(id=bot_id, username=username)
    return bot_api


def make_telegram_bot(
    establishment_id: uuid.UUID,
    bot_id: int = 123456789,
    bot_token: str = TOKEN,
) -> TelegramBot:
    now = datetime.now(UTC)
    return TelegramBot(
        establishment_id=establishment_id,
        bot_id=bot_id,
        bot_username="barbearia_bot",
        bot_token=bot_token,
        webhook_secret="segredo-antigo",
        created_at=now,
        updated_at=now,
    )


def make_actor(
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
    is_global_admin: bool = False,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=memberships
    )
