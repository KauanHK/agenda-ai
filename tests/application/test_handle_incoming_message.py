"""Testes de `HandleIncomingMessage`: sempre sai uma resposta, e uma só."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.application.use_cases.handle_incoming_message import HandleIncomingMessage
from src.application.use_cases.open_booking_session import BookingSessionProvider
from src.domain.entities import (
    AgentAnswer,
    BookingSession,
    Channel,
    Contact,
    IncomingMessage,
)
from src.domain.exceptions import (
    AgentError,
    BookingSessionError,
    ClientBlockedError,
)
from tests.fakes.agent_runner import FakeAgentRunner
from tests.fakes.messenger import FakeMessenger
from tests.fakes.phone_resolver import FakePhoneResolver
from tests.fakes.session_cache import FakeSessionCache
from tests.fakes.session_issuer import FakeSessionIssuer
from tests.fakes.tool_provider import FakeToolProvider

_NOW = datetime(2026, 8, 30, 9, 0, tzinfo=UTC)
_PHONE = "5547999123456"


def _contact() -> Contact:
    return Contact(
        channel=Channel.TELEGRAM,
        channel_user_id="42",
        display_name="Kauan",
        phone=_PHONE,
    )


def _message(text: str = "quero marcar um horário") -> IncomingMessage:
    return IncomingMessage(
        contact=_contact(),
        text=text,
        channel_message_id="1001",
        received_at=_NOW,
    )


def _session() -> BookingSession:
    return BookingSession(
        token="jwt-da-sessao",
        phone=_PHONE,
        client_id=uuid.UUID("01a04f64-0000-7000-8000-000000000000"),
        client_name="Kauan Kaestner",
        expires_at=_NOW + timedelta(minutes=10),
        is_new_client=True,
    )


def _session_provider(
    *,
    issuer: FakeSessionIssuer | None = None,
) -> BookingSessionProvider:
    return BookingSessionProvider(
        phone_resolver=FakePhoneResolver(_PHONE),
        issuer=issuer or FakeSessionIssuer(_session()),
        cache=FakeSessionCache(),
        clock=lambda: _NOW,
        refresh_margin_seconds=60,
    )


def _handler(
    *,
    session_provider: BookingSessionProvider | None = None,
    tool_provider: FakeToolProvider | None = None,
    agent: FakeAgentRunner | None = None,
    messenger: FakeMessenger | None = None,
) -> HandleIncomingMessage:
    default_answer = AgentAnswer(text="Temos corte às 14h. Confirma?", tool_calls_made=1)
    return HandleIncomingMessage(
        session_provider or _session_provider(),
        tool_provider or FakeToolProvider(["list_services"]),
        agent or FakeAgentRunner(default_answer),
        messenger or FakeMessenger(),
        clock=lambda: _NOW,
    )


async def test_caminho_feliz_envia_uma_resposta_uma_vez() -> None:
    messenger = FakeMessenger()
    agent = FakeAgentRunner(AgentAnswer(text="Confirmado para amanhã às 14h.", tool_calls_made=2))

    await _handler(agent=agent, messenger=messenger).execute(_message())

    assert messenger.sent == [(_contact(), "Confirmado para amanhã às 14h.")]
    assert messenger.typing_signals == [_contact()]


async def test_passa_tools_da_sessao_e_o_contexto_do_turno_ao_agente() -> None:
    agent = FakeAgentRunner()
    tool_provider = FakeToolProvider(["list_services", "create_scheduling"])

    await _handler(agent=agent, tool_provider=tool_provider).execute(_message("oi"))

    (conversation, user_text, tools, context) = agent.calls[0]
    assert conversation.thread_id == "telegram:42"
    assert user_text == "oi"
    assert list(tools) == ["list_services", "create_scheduling"]
    assert tool_provider.tokens == ["jwt-da-sessao"]
    assert context.client_name == "Kauan Kaestner"
    assert context.now == _NOW
    assert context.is_new_client is True


async def test_booking_session_error_responde_ao_cliente_e_nao_roda_o_agente() -> None:
    issuer = FakeSessionIssuer(error=BookingSessionError("AgendaBot fora do ar"))
    agent = FakeAgentRunner()
    messenger = FakeMessenger()

    await _handler(
        session_provider=_session_provider(issuer=issuer),
        agent=agent,
        messenger=messenger,
    ).execute(_message())

    assert messenger.sent == [(_contact(), AgentError.user_message)]
    assert agent.calls == []


async def test_client_blocked_error_usa_a_mensagem_especifica() -> None:
    issuer = FakeSessionIssuer(error=ClientBlockedError("inativo"))
    messenger = FakeMessenger()

    await _handler(
        session_provider=_session_provider(issuer=issuer),
        messenger=messenger,
    ).execute(_message())

    assert messenger.sent == [(_contact(), ClientBlockedError.user_message)]


async def test_erro_inesperado_no_runner_responde_frase_padrao_sem_vazar(
    caplog: pytest.LogCaptureFixture,
) -> None:
    agent = FakeAgentRunner(error=RuntimeError("detalhe interno com token secreto"))
    messenger = FakeMessenger()

    with caplog.at_level(logging.ERROR):
        await _handler(agent=agent, messenger=messenger).execute(_message())

    assert messenger.sent == [(_contact(), AgentError.user_message)]
    assert "token secreto" not in messenger.sent[0][1]
    assert any(record.exc_info for record in caplog.records)


async def test_falha_em_signal_typing_nao_impede_a_resposta() -> None:
    messenger = FakeMessenger(typing_error=RuntimeError("sendChatAction caiu"))
    agent = FakeAgentRunner(AgentAnswer(text="Beleza!", tool_calls_made=0))

    await _handler(agent=agent, messenger=messenger).execute(_message())

    assert messenger.sent == [(_contact(), "Beleza!")]
