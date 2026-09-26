import uuid
from typing import Protocol

from app.modules.channels.domain.entities import NewTelegramBot, TelegramBot


class TelegramBotsRepositoryProtocol(Protocol):
    async def get_by_establishment(
        self,
        establishment_id: uuid.UUID,
    ) -> TelegramBot | None: ...

    async def get_by_bot_id(self, bot_id: int) -> TelegramBot | None: ...

    async def save(self, bot: NewTelegramBot) -> TelegramBot: ...

    async def delete(self, establishment_id: uuid.UUID) -> None: ...
