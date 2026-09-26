import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.roles import UserRole
from app.modules.channels.application.use_cases.connect_telegram import (
    TelegramBotConnector,
)
from app.modules.channels.domain.exceptions import (
    InvalidBotTokenError,
    TelegramApiError,
)
from tests.modules.channels.fakes import (
    BASE_URL,
    OTHER_TOKEN,
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
def uow() -> FakeChannelsUnitOfWork:
    return FakeChannelsUnitOfWork()


@pytest.fixture
def bot_api():
    return make_bot_api()


@pytest.fixture
def connector(uow, bot_api) -> TelegramBotConnector:
    return TelegramBotConnector(uow=uow, bot_api=bot_api, webhook_base_url=BASE_URL)


@pytest.fixture
def admin(establishment_id):
    return make_actor(establishment_id, UserRole.ESTABLISHMENT_ADMIN)


async def test_connect_saves_bot_and_registers_webhook(
    connector, uow, bot_api, admin, establishment_id
):
    await connector.connect(admin, establishment_id, TOKEN)

    bot_api.get_me.assert_awaited_once_with(TOKEN)
    set_webhook = bot_api.set_webhook.await_args
    assert set_webhook.args == (TOKEN,)
    assert set_webhook.kwargs["url"] == (
        f"{BASE_URL}/webhook/telegram/{establishment_id}"
    )
    saved = uow.telegram_bots.save.await_args.args[0]
    assert saved.establishment_id == establishment_id
    assert saved.bot_id == 123456789
    assert saved.bot_username == "barbearia_bot"
    assert saved.bot_token == TOKEN
    assert saved.webhook_secret == set_webhook.kwargs["secret_token"]
    bot_api.delete_webhook.assert_not_awaited()
    assert uow.committed


async def test_reconnect_same_bot_rotates_secret(
    connector, uow, bot_api, admin, establishment_id
):
    current = make_telegram_bot(establishment_id)
    uow.telegram_bots.get_by_bot_id.return_value = current
    uow.telegram_bots.get_by_establishment.return_value = current

    await connector.connect(admin, establishment_id, TOKEN)

    saved = uow.telegram_bots.save.await_args.args[0]
    assert saved.webhook_secret != current.webhook_secret
    bot_api.delete_webhook.assert_not_awaited()


async def test_switch_bot_deletes_old_webhook(
    connector, uow, bot_api, admin, establishment_id
):
    uow.telegram_bots.get_by_establishment.return_value = make_telegram_bot(
        establishment_id, bot_id=111, bot_token=OTHER_TOKEN
    )

    await connector.connect(admin, establishment_id, TOKEN)

    bot_api.delete_webhook.assert_awaited_once_with(
        OTHER_TOKEN, drop_pending_updates=False
    )
    uow.telegram_bots.save.assert_awaited_once()


@pytest.mark.parametrize("error", [TelegramApiError, InvalidBotTokenError])
async def test_switch_bot_ignores_delete_webhook_failure(
    connector, uow, bot_api, admin, establishment_id, error
):
    uow.telegram_bots.get_by_establishment.return_value = make_telegram_bot(
        establishment_id, bot_id=111, bot_token=OTHER_TOKEN
    )
    bot_api.delete_webhook.side_effect = error("falhou")

    await connector.connect(admin, establishment_id, TOKEN)

    uow.telegram_bots.save.assert_awaited_once()
    assert uow.committed


async def test_bot_of_other_establishment_conflicts(
    connector, uow, bot_api, admin, establishment_id
):
    uow.telegram_bots.get_by_bot_id.return_value = make_telegram_bot(uuid.uuid7())

    with pytest.raises(ConflictError):
        await connector.connect(admin, establishment_id, TOKEN)

    bot_api.set_webhook.assert_not_awaited()
    uow.telegram_bots.save.assert_not_awaited()


async def test_concurrent_connect_unique_violation_conflicts(
    connector, uow, admin, establishment_id
):
    uow.telegram_bots.save.side_effect = IntegrityError("insert", {}, Exception())

    with pytest.raises(ConflictError):
        await connector.connect(admin, establishment_id, TOKEN)


async def test_rejected_token_saves_nothing(
    connector, uow, bot_api, admin, establishment_id
):
    bot_api.get_me.side_effect = InvalidBotTokenError("recusado")

    with pytest.raises(InvalidBotTokenError):
        await connector.connect(admin, establishment_id, TOKEN)

    bot_api.set_webhook.assert_not_awaited()
    uow.telegram_bots.save.assert_not_awaited()


async def test_set_webhook_failure_saves_nothing(
    connector, uow, bot_api, admin, establishment_id
):
    bot_api.set_webhook.side_effect = TelegramApiError("falhou")

    with pytest.raises(TelegramApiError):
        await connector.connect(admin, establishment_id, TOKEN)

    uow.telegram_bots.save.assert_not_awaited()
    assert not uow.committed


async def test_missing_establishment_not_found(
    connector, uow, bot_api, admin, establishment_id
):
    uow.establishments.get_by_id_or_none.return_value = None

    with pytest.raises(NotFoundError):
        await connector.connect(admin, establishment_id, TOKEN)

    bot_api.set_webhook.assert_not_awaited()


async def test_member_forbidden(connector, bot_api, establishment_id):
    member = make_actor(establishment_id, UserRole.MEMBER)

    with pytest.raises(ForbiddenError):
        await connector.connect(member, establishment_id, TOKEN)

    bot_api.get_me.assert_not_awaited()


async def test_admin_of_other_establishment_forbidden(connector, establishment_id):
    other_admin = make_actor(uuid.uuid7(), UserRole.ESTABLISHMENT_ADMIN)

    with pytest.raises(ForbiddenError):
        await connector.connect(other_admin, establishment_id, TOKEN)


async def test_global_admin_can_connect(connector, uow, establishment_id):
    await connector.connect(make_actor(is_global_admin=True), establishment_id, TOKEN)

    uow.telegram_bots.save.assert_awaited_once()
