import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.roles import UserRole
from app.modules.channels.application.use_cases.disconnect_telegram import (
    TelegramBotDisconnector,
)
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)
from tests.modules.channels.fakes import (
    TOKEN,
    FakeChannelsUnitOfWork,
    make_actor,
    make_bot_api,
    make_telegram_bot,
)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def uow(establishment_id) -> FakeChannelsUnitOfWork:
    uow = FakeChannelsUnitOfWork()
    uow.telegram_bots.get_by_establishment.return_value = make_telegram_bot(
        establishment_id
    )
    return uow


@pytest.fixture
def bot_api():
    return make_bot_api()


@pytest.fixture
def disconnector(uow, bot_api) -> TelegramBotDisconnector:
    return TelegramBotDisconnector(uow=uow, bot_api=bot_api)


@pytest.fixture
def admin(establishment_id):
    return make_actor(establishment_id, UserRole.ESTABLISHMENT_ADMIN)


async def test_disconnect_deletes_webhook_and_bot(
    disconnector, uow, bot_api, admin, establishment_id
):
    await disconnector.disconnect(admin, establishment_id)

    bot_api.delete_webhook.assert_awaited_once_with(TOKEN, drop_pending_updates=True)
    uow.telegram_bots.delete.assert_awaited_once_with(establishment_id)
    assert uow.committed


async def test_revoked_token_still_deletes_bot(
    disconnector, uow, bot_api, admin, establishment_id
):
    bot_api.delete_webhook.side_effect = InvalidBotTokenError("revogado")

    await disconnector.disconnect(admin, establishment_id)

    uow.telegram_bots.delete.assert_awaited_once_with(establishment_id)
    assert uow.committed


async def test_telegram_failure_keeps_bot(
    disconnector, uow, bot_api, admin, establishment_id
):
    bot_api.delete_webhook.side_effect = TelegramApiError("falhou")

    with pytest.raises(TelegramApiError):
        await disconnector.disconnect(admin, establishment_id)

    uow.telegram_bots.delete.assert_not_awaited()
    assert not uow.committed


async def test_without_bot_not_found(
    disconnector, uow, bot_api, admin, establishment_id
):
    uow.telegram_bots.get_by_establishment.return_value = None

    with pytest.raises(NotFoundError):
        await disconnector.disconnect(admin, establishment_id)

    bot_api.delete_webhook.assert_not_awaited()


async def test_member_forbidden(disconnector, uow, bot_api, establishment_id):
    member = make_actor(establishment_id, UserRole.MEMBER)

    with pytest.raises(ForbiddenError):
        await disconnector.disconnect(member, establishment_id)

    bot_api.delete_webhook.assert_not_awaited()
    uow.telegram_bots.delete.assert_not_awaited()


async def test_global_admin_can_disconnect(disconnector, uow, establishment_id):
    await disconnector.disconnect(make_actor(is_global_admin=True), establishment_id)

    uow.telegram_bots.delete.assert_awaited_once_with(establishment_id)
