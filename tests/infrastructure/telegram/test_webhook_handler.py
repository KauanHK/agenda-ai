"""Testes de `TelegramWebhookHandler`: parse -> comando ou agente."""

from datetime import UTC, datetime
from typing import Any

from src.domain.entities import Channel, Contact, IncomingMessage
from src.domain.exceptions import ConversationStateError
from src.infrastructure.telegram.commands import RESET_MESSAGE, WELCOME_MESSAGE
from src.infrastructure.telegram.webhook_handler import TelegramWebhookHandler
from tests.fakes.messenger import FakeMessenger

_CONTACT = Contact(
    channel=Channel.TELEGRAM,
    channel_user_id="42",
    display_name="Kauan",
    phone="5547999111222",
)


def _message(text: str) -> IncomingMessage:
    return IncomingMessage(
        contact=_CONTACT,
        text=text,
        channel_message_id="1",
        received_at=datetime(2026, 8, 30, 9, 0, tzinfo=UTC),
    )


class _StubIncomingHandler:
    def __init__(self) -> None:
        self.handled: list[IncomingMessage] = []

    async def execute(self, message: IncomingMessage) -> None:
        self.handled.append(message)


class _StubReset:
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error
        self.calls: list[Any] = []

    async def execute(self, conversation: Any) -> None:
        self.calls.append(conversation)
        if self._error is not None:
            raise self._error


def _handler(
    *,
    parsed: IncomingMessage | None,
    incoming: _StubIncomingHandler | None = None,
    reset: _StubReset | None = None,
    messenger: FakeMessenger | None = None,
) -> tuple[TelegramWebhookHandler, _StubIncomingHandler, _StubReset, FakeMessenger]:
    incoming = incoming or _StubIncomingHandler()
    reset = reset or _StubReset()
    messenger = messenger or FakeMessenger()
    handler = TelegramWebhookHandler(
        parse_update=lambda _payload: parsed,
        handle_incoming_message=incoming,  # type: ignore[arg-type]
        reset_conversation=reset,  # type: ignore[arg-type]
        messenger=messenger,
    )
    return handler, incoming, reset, messenger


async def test_mensagem_normal_vai_para_o_agente() -> None:
    handler, incoming, reset, messenger = _handler(parsed=_message("quero marcar"))

    await handler.handle_update({"update_id": 1})

    assert [m.text for m in incoming.handled] == ["quero marcar"]
    assert reset.calls == []
    assert messenger.sent == []


async def test_start_reseta_e_manda_boas_vindas() -> None:
    handler, incoming, reset, messenger = _handler(parsed=_message("/start"))

    await handler.handle_update({"update_id": 1})

    assert len(reset.calls) == 1
    assert reset.calls[0].thread_id == "telegram:42"
    assert messenger.sent == [(_CONTACT, WELCOME_MESSAGE)]
    assert incoming.handled == []


async def test_reset_reseta_e_confirma() -> None:
    handler, _incoming, reset, messenger = _handler(parsed=_message("/reset"))

    await handler.handle_update({"update_id": 1})

    assert len(reset.calls) == 1
    assert messenger.sent == [(_CONTACT, RESET_MESSAGE)]


async def test_comando_desconhecido_vai_para_o_agente() -> None:
    handler, incoming, reset, _messenger = _handler(parsed=_message("/ajuda por favor"))

    await handler.handle_update({"update_id": 1})

    assert [m.text for m in incoming.handled] == ["/ajuda por favor"]
    assert reset.calls == []


async def test_update_ignorado_nao_faz_nada() -> None:
    handler, incoming, reset, messenger = _handler(parsed=None)

    await handler.handle_update({"update_id": 1})

    assert incoming.handled == []
    assert reset.calls == []
    assert messenger.sent == []


async def test_falha_no_reset_responde_ao_cliente_sem_boas_vindas() -> None:
    reset = _StubReset(error=ConversationStateError("Redis fora"))
    handler, _incoming, _reset, messenger = _handler(parsed=_message("/reset"), reset=reset)

    await handler.handle_update({"update_id": 1})

    assert messenger.sent == [(_CONTACT, ConversationStateError.user_message)]


async def test_handle_update_nunca_levanta() -> None:
    def _boom(_payload: Any) -> None:
        raise RuntimeError("parser explodiu")

    handler = TelegramWebhookHandler(
        parse_update=_boom,
        handle_incoming_message=_StubIncomingHandler(),  # type: ignore[arg-type]
        reset_conversation=_StubReset(),  # type: ignore[arg-type]
        messenger=FakeMessenger(),
    )

    await handler.handle_update({"update_id": 1})  # não levanta
