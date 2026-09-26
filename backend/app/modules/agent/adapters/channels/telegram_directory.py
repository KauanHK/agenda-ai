"""Diretório de canais lido direto do banco, pelo módulo `channels`."""

import uuid
from collections.abc import Callable
from zoneinfo import ZoneInfo

from sqlalchemy.exc import SQLAlchemyError

from app.modules.agent.domain.entities import Establishment, TelegramChannel
from app.modules.agent.domain.exceptions import ChannelLookupError
from app.modules.channels.adapters.db.factories import make_unit_of_work
from app.modules.channels.application.ports.unit_of_work import (
    ChannelsUnitOfWorkProtocol,
)


class DbTelegramChannelDirectory:
    """Implementa `TelegramChannelDirectoryProtocol` consultando o banco a cada chamada.

    Sem cache de propósito: são duas buscas por chave primária e uma decifragem, e
    com cache reconectar ou desconectar o bot só valeria depois do TTL.
    """

    def __init__(
        self,
        uow_factory: Callable[[], ChannelsUnitOfWorkProtocol] = make_unit_of_work,
    ) -> None:
        self._uow_factory = uow_factory

    async def get(self, establishment_id: uuid.UUID) -> TelegramChannel | None:
        """Devolve o bot do estabelecimento, ou `None` se ele não atende."""
        try:
            async with self._uow_factory() as uow:
                bot = await uow.telegram_bots.get_by_establishment(establishment_id)
                if bot is None:
                    return None
                establishment = await uow.establishments.get_by_id_or_none(
                    establishment_id
                )
        except (SQLAlchemyError, OSError) as exc:
            raise ChannelLookupError("Não foi possível consultar o canal.") from exc

        if establishment is None or not establishment.is_active:
            return None

        return TelegramChannel(
            establishment=Establishment(
                id=establishment.id, timezone=ZoneInfo(establishment.timezone)
            ),
            bot_token=bot.bot_token,
            webhook_secret=bot.webhook_secret,
        )
