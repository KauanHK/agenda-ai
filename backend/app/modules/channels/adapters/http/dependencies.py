from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.core.settings import settings
from app.modules.channels.adapters.db.factories import make_unit_of_work
from app.modules.channels.adapters.db.unit_of_work import ChannelsUnitOfWork
from app.modules.channels.adapters.telegram.bot_api import (
    TelegramBotApi,
    build_bot_api_client,
)
from app.modules.channels.application.use_cases.connect_telegram import (
    TelegramBotConnector,
)
from app.modules.channels.application.use_cases.read_telegram import (
    TelegramBotReader,
)

ChannelsUnitOfWorkDep = Annotated[ChannelsUnitOfWork, Depends(make_unit_of_work)]


async def get_bot_api() -> AsyncIterator[TelegramBotApi]:
    # Um client por requisição: conectar é raro, e um client global não se paga.
    async with build_bot_api_client() as client:
        yield TelegramBotApi(client)


def get_telegram_bot_reader(uow: ChannelsUnitOfWorkDep) -> TelegramBotReader:
    return TelegramBotReader(uow=uow)


def get_telegram_bot_connector(
    uow: ChannelsUnitOfWorkDep,
    bot_api: Annotated[TelegramBotApi, Depends(get_bot_api)],
) -> TelegramBotConnector:
    return TelegramBotConnector(
        uow=uow,
        bot_api=bot_api,
        webhook_base_url=settings.TELEGRAM_WEBHOOK_BASE_URL,
    )


TelegramBotReaderDep = Annotated[TelegramBotReader, Depends(get_telegram_bot_reader)]
TelegramBotConnectorDep = Annotated[
    TelegramBotConnector, Depends(get_telegram_bot_connector)
]
