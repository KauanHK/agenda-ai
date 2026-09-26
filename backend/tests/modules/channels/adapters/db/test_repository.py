import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.secret_box import decrypt, encrypt
from app.modules.channels.adapters.db.models import TelegramBot as TelegramBotModel
from app.modules.channels.adapters.db.repository import TelegramBotsRepository
from app.modules.channels.domain.entities import NewTelegramBot, TelegramBot

TOKEN = "123456:ABC-token"
SECRET = "segredo-do-webhook"


@pytest.fixture
def session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return session


@pytest.fixture
def repo(session: AsyncMock) -> TelegramBotsRepository:
    return TelegramBotsRepository(session=session)


@pytest.fixture
def model_row() -> TelegramBotModel:
    now = datetime.now(UTC)
    return TelegramBotModel(
        establishment_id=uuid.uuid7(),
        bot_id=123456,
        bot_username="agenda_bot",
        bot_token_encrypted=encrypt(TOKEN),
        webhook_secret_encrypted=encrypt(SECRET),
        created_at=now,
        updated_at=now,
    )


def _new_bot(establishment_id: uuid.UUID) -> NewTelegramBot:
    return NewTelegramBot(
        establishment_id=establishment_id,
        bot_id=123456,
        bot_username="agenda_bot",
        bot_token=TOKEN,
        webhook_secret=SECRET,
    )


async def test_get_by_establishment_returns_decrypted_entity(repo, session, model_row):
    session.get.return_value = model_row

    result = await repo.get_by_establishment(model_row.establishment_id)

    assert isinstance(result, TelegramBot)
    assert result.bot_token == TOKEN
    assert result.webhook_secret == SECRET


async def test_get_by_establishment_returns_none(repo, session):
    session.get.return_value = None

    assert await repo.get_by_establishment(uuid.uuid7()) is None


async def test_get_by_bot_id_returns_decrypted_entity(repo, session, model_row):
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = model_row
    session.execute.return_value = result_mock

    result = await repo.get_by_bot_id(model_row.bot_id)

    assert result is not None
    assert result.bot_token == TOKEN


async def test_save_inserts_encrypted_row(repo, session):
    session.get.return_value = None
    establishment_id = uuid.uuid7()

    result = await repo.save(_new_bot(establishment_id))

    row = session.add.call_args.args[0]
    assert isinstance(row, TelegramBotModel)
    assert row.establishment_id == establishment_id
    assert TOKEN not in row.bot_token_encrypted
    assert SECRET not in row.webhook_secret_encrypted
    assert decrypt(row.bot_token_encrypted) == TOKEN
    assert decrypt(row.webhook_secret_encrypted) == SECRET
    assert result.bot_token == TOKEN
    assert result.webhook_secret == SECRET


async def test_save_replaces_existing_row(repo, session, model_row):
    session.get.return_value = model_row

    await repo.save(
        NewTelegramBot(
            establishment_id=model_row.establishment_id,
            bot_id=999,
            bot_username="outro_bot",
            bot_token="999:novo-token",
            webhook_secret="novo-segredo",
        )
    )

    session.add.assert_not_called()
    assert model_row.bot_id == 999
    assert model_row.bot_username == "outro_bot"
    assert decrypt(model_row.bot_token_encrypted) == "999:novo-token"
    assert decrypt(model_row.webhook_secret_encrypted) == "novo-segredo"


async def test_delete_executes_statement(repo, session):
    await repo.delete(uuid.uuid7())

    session.execute.assert_awaited_once()
