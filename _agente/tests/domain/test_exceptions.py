"""Testes do catálogo de erros do domínio."""

import pytest

from src.domain.exceptions import (
    AgentError,
    AgentUnavailableError,
    BookingSessionError,
    ClientBlockedError,
    ConversationStateError,
    DeliveryError,
    InvalidPhoneError,
)

_ALL_ERRORS: list[type[AgentError]] = [
    AgentError,
    AgentUnavailableError,
    BookingSessionError,
    ClientBlockedError,
    ConversationStateError,
    DeliveryError,
    InvalidPhoneError,
]


@pytest.mark.parametrize("error_cls", _ALL_ERRORS)
def test_todo_erro_carrega_um_user_message_nao_vazio(error_cls: type[AgentError]) -> None:
    assert error_cls().user_message.strip()


@pytest.mark.parametrize("error_cls", _ALL_ERRORS)
def test_todo_erro_deriva_de_agent_error(error_cls: type[AgentError]) -> None:
    assert issubclass(error_cls, AgentError)


def test_client_blocked_tem_mensagem_propria() -> None:
    assert ClientBlockedError.user_message != AgentError.user_message
    assert "estabelecimento" in ClientBlockedError().user_message.lower()


def test_client_blocked_e_um_booking_session_error() -> None:
    assert issubclass(ClientBlockedError, BookingSessionError)
    assert issubclass(BookingSessionError, AgentError)
