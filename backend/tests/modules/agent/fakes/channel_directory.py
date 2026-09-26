"""Fake de `TelegramChannelDirectoryProtocol`: canais em memória, por estabelecimento."""

import uuid

from app.modules.agent.domain.entities import TelegramChannel
from app.modules.agent.domain.exceptions import ChannelLookupError


class FakeChannelDirectory:
    """Devolve o canal cadastrado, `None` se não houver, ou levanta sob demanda."""

    def __init__(self, *channels: TelegramChannel, fail: bool = False) -> None:
        self.channels = {channel.establishment.id: channel for channel in channels}
        self.fail = fail

    async def get(self, establishment_id: uuid.UUID) -> TelegramChannel | None:
        if self.fail:
            raise ChannelLookupError("banco fora")
        return self.channels.get(establishment_id)
