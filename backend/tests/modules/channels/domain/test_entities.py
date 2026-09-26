import uuid
from datetime import UTC, datetime

from app.modules.channels.domain.entities import NewTelegramBot, TelegramBot

TOKEN = "123456:ABC-token"
SECRET = "segredo-do-webhook"


def test_new_telegram_bot_repr_hides_secrets():
    bot = NewTelegramBot(
        establishment_id=uuid.uuid7(),
        bot_id=123456,
        bot_username="agenda_bot",
        bot_token=TOKEN,
        webhook_secret=SECRET,
    )

    text = repr(bot)

    assert TOKEN not in text
    assert SECRET not in text
    assert "agenda_bot" in text


def test_telegram_bot_repr_hides_secrets():
    now = datetime.now(UTC)
    bot = TelegramBot(
        establishment_id=uuid.uuid7(),
        bot_id=123456,
        bot_username="agenda_bot",
        bot_token=TOKEN,
        webhook_secret=SECRET,
        created_at=now,
        updated_at=now,
    )

    text = repr(bot)

    assert TOKEN not in text
    assert SECRET not in text
