import uuid

from app.core.actors.user import UserActor
from app.modules.channels.application.authz import assert_can_read
from app.modules.channels.application.ports.unit_of_work import (
    ChannelsUnitOfWorkProtocol,
)
from app.modules.channels.domain.entities import TelegramBot


class TelegramBotReader:
    def __init__(self, uow: ChannelsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get(
        self,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> TelegramBot | None:
        """Bot conectado ao estabelecimento, ou `None` se não houver."""

        assert_can_read(actor, establishment_id)

        async with self._uow as uow:
            return await uow.telegram_bots.get_by_establishment(establishment_id)
