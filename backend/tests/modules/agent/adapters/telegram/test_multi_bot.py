"""De ponta a ponta no handler: dois estabelecimentos, cada um com o seu bot.

Parser, caso de uso e messenger reais; só a sessão, as tools, o LLM e a Bot API são
dublês. O mesmo usuário do Telegram (mesmo `chat_id`) fala com os dois bots.
"""

import functools
import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

from app.modules.agent.adapters.telegram.client import (
    TelegramMessenger,
    build_telegram_client,
)
from app.modules.agent.adapters.telegram.update_parser import parse_update
from app.modules.agent.adapters.telegram.webhook_handler import TelegramWebhookHandler
from app.modules.agent.application.use_cases.handle_incoming_message import (
    HandleIncomingMessage,
)
from app.modules.agent.application.use_cases.open_booking_session import (
    BookingSessionProvider,
)
from app.modules.agent.domain.entities import (
    BookingSession,
    Establishment,
    TelegramChannel,
)
from tests.modules.agent.fakes.agent_runner import FakeAgentRunner
from tests.modules.agent.fakes.channel_directory import FakeChannelDirectory
from tests.modules.agent.fakes.phone_resolver import FakePhoneResolver
from tests.modules.agent.fakes.session_cache import FakeSessionCache
from tests.modules.agent.fakes.tool_provider import FakeToolProvider

_NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
_PHONE = "5547999000042"


def _channel(suffix: str, bot_token: str) -> TelegramChannel:
    return TelegramChannel(
        establishment=Establishment(
            id=uuid.UUID(f"01a04f64-0000-7000-8000-00000000e00{suffix}"),
            timezone=ZoneInfo("America/Sao_Paulo"),
        ),
        bot_token=bot_token,
        webhook_secret=f"segredo-{suffix}",
    )


_A = _channel("1", "111:token-a")
_B = _channel("2", "222:token-b")


def _send_url(channel: TelegramChannel) -> str:
    return f"https://api.telegram.org/bot{channel.bot_token}/sendMessage"


class _PerEstablishmentIssuer:
    """Emite uma sessão para o estabelecimento pedido e registra qual foi."""

    def __init__(self) -> None:
        self.establishments: list[uuid.UUID] = []

    async def issue(
        self, establishment_id: uuid.UUID, phone: str, name: str | None
    ) -> BookingSession:
        self.establishments.append(establishment_id)
        return BookingSession(
            token=f"sessao-{establishment_id}",
            establishment_id=establishment_id,
            phone=phone,
            client_id=uuid.uuid4(),
            client_name=name or "Cliente",
            expires_at=_NOW + timedelta(minutes=10),
            is_new_client=False,
        )


def _update(text: str) -> dict[str, object]:
    return {
        "update_id": 1,
        "message": {
            "message_id": 7,
            "date": int(_NOW.timestamp()),
            "text": text,
            "chat": {"id": 42, "type": "private"},
            "from": {"id": 42, "is_bot": False, "first_name": "Kauan"},
        },
    }


@pytest.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with build_telegram_client(
        api_root="https://api.telegram.org",
        connect_timeout_seconds=5.0,
        read_timeout_seconds=5.0,
    ) as client:
        yield client


async def test_mesmo_chat_id_nos_dois_bots_fica_em_estabelecimentos_separados(
    http_client: httpx.AsyncClient,
) -> None:
    issuer = _PerEstablishmentIssuer()
    runner = FakeAgentRunner()
    messenger = TelegramMessenger(http_client, FakeChannelDirectory(_A, _B))
    phone_resolver = FakePhoneResolver(_PHONE)
    handler = TelegramWebhookHandler(
        parse_update=functools.partial(parse_update, phone_resolver=phone_resolver),
        handle_incoming_message=HandleIncomingMessage(
            BookingSessionProvider(
                phone_resolver=phone_resolver,
                issuer=issuer,
                cache=FakeSessionCache(),
                clock=lambda: _NOW,
                refresh_margin_seconds=60,
            ),
            FakeToolProvider(),
            runner,
            messenger,
            clock=lambda: _NOW,
        ),
        reset_conversation=None,  # type: ignore[arg-type]
        messenger=messenger,
    )

    with respx.mock:
        respx.post(url__regex=r".*/sendChatAction").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        route_a = respx.post(_send_url(_A)).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        route_b = respx.post(_send_url(_B)).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await handler.handle_update(_A.establishment, _update("oi A"))
        await handler.handle_update(_B.establishment, _update("oi B"))

    threads = [conversation.thread_id for conversation, *_ in runner.calls]
    assert threads == [
        f"telegram:{_A.establishment.id}:42",
        f"telegram:{_B.establishment.id}:42",
    ]
    assert issuer.establishments == [_A.establishment.id, _B.establishment.id]
    assert route_a.call_count == 1
    assert route_b.call_count == 1
    assert json.loads(route_a.calls.last.request.content)["chat_id"] == "42"
    assert json.loads(route_b.calls.last.request.content)["chat_id"] == "42"
