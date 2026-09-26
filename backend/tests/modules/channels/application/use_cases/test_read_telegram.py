import uuid

import pytest

from app.core.exceptions import ForbiddenError
from app.core.roles import UserRole
from app.modules.channels.application.use_cases.read_telegram import (
    TelegramBotReader,
)
from tests.modules.channels.fakes import (
    FakeChannelsUnitOfWork,
    make_actor,
    make_telegram_bot,
)


async def test_member_reads_bot():
    establishment_id = uuid.uuid7()
    uow = FakeChannelsUnitOfWork()
    bot = make_telegram_bot(establishment_id)
    uow.telegram_bots.get_by_establishment.return_value = bot

    result = await TelegramBotReader(uow).get(
        make_actor(establishment_id, UserRole.MEMBER), establishment_id
    )

    assert result == bot


async def test_global_admin_reads_bot():
    result = await TelegramBotReader(FakeChannelsUnitOfWork()).get(
        make_actor(is_global_admin=True), uuid.uuid7()
    )

    assert result is None


async def test_non_member_forbidden():
    with pytest.raises(ForbiddenError):
        await TelegramBotReader(FakeChannelsUnitOfWork()).get(
            make_actor(uuid.uuid7(), UserRole.ESTABLISHMENT_ADMIN), uuid.uuid7()
        )
