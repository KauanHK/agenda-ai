"""Testes das entidades do domínio."""

import dataclasses
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from app.modules.agent.domain.entities import (
    AgentAnswer,
    AgentContext,
    Channel,
    Contact,
    ConversationRef,
    Establishment,
    IncomingMessage,
)

_ESTABLISHMENT_A = uuid.UUID("01a04f64-0000-7000-8000-00000000e001")
_ESTABLISHMENT_B = uuid.UUID("01a04f64-0000-7000-8000-00000000e002")


class TestConversationRef:
    def test_thread_id_tem_canal_estabelecimento_e_usuario(self) -> None:
        ref = ConversationRef(
            channel=Channel.TELEGRAM,
            establishment_id=_ESTABLISHMENT_A,
            channel_user_id="123456",
        )
        assert ref.thread_id == f"telegram:{_ESTABLISHMENT_A}:123456"

    def test_thread_id_e_estavel_para_a_mesma_conversa(self) -> None:
        a = ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_A, "999")
        b = ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_A, "999")
        assert a.thread_id == b.thread_id

    def test_thread_id_isola_por_estabelecimento(self) -> None:
        # No Telegram, o `chat_id` privado é o id do usuário, igual em todos os bots.
        a = ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_A, "42")
        b = ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_B, "42")
        assert a.thread_id != b.thread_id


def test_contact_e_imutavel() -> None:
    contact = Contact(
        channel=Channel.TELEGRAM,
        channel_user_id="1",
        display_name="Kauan",
        phone="5547999000001",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        contact.phone = "outro"  # type: ignore[misc]


def test_incoming_message_guarda_o_contato_e_o_texto() -> None:
    contact = Contact(Channel.TELEGRAM, "1", None, "5547999000001")
    message = IncomingMessage(
        establishment=Establishment(_ESTABLISHMENT_A, ZoneInfo("America/Sao_Paulo")),
        contact=contact,
        text="quero marcar um horário",
        channel_message_id="10",
        received_at=datetime(2026, 8, 29, 9, 30, tzinfo=UTC),
    )
    assert message.contact is contact
    assert message.text == "quero marcar um horário"
    assert message.conversation == ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_A, "1")


def test_agent_answer_conta_as_tool_calls_do_turno() -> None:
    assert AgentAnswer(text="pronto", tool_calls_made=3).tool_calls_made == 3


def test_agent_context_e_imutavel() -> None:
    context = AgentContext(
        client_name="Kauan",
        now=datetime(2026, 8, 28, 9, 0, tzinfo=UTC),
        is_new_client=True,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.client_name = "outro"  # type: ignore[misc]
