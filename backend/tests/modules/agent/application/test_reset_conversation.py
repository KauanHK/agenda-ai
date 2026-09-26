"""Testes de `ResetConversation`: apaga a thread certa e propaga a falha do Redis."""

import uuid

import pytest

from app.modules.agent.application.use_cases.reset_conversation import ResetConversation
from app.modules.agent.domain.entities import Channel, ConversationRef
from app.modules.agent.domain.exceptions import ConversationStateError
from tests.modules.agent.fakes.conversation_history import FakeConversationHistory

_ESTABLISHMENT_ID = uuid.UUID("01a04f64-0000-7000-8000-00000000e001")
_REF = ConversationRef(Channel.TELEGRAM, _ESTABLISHMENT_ID, "42")


async def test_apaga_o_historico_da_conversa() -> None:
    history = FakeConversationHistory()

    await ResetConversation(history).execute(_REF)

    assert history.cleared == [_REF]


async def test_propaga_a_falha_ao_apagar_o_historico() -> None:
    history = FakeConversationHistory(error=ConversationStateError("Redis recusou"))

    with pytest.raises(ConversationStateError):
        await ResetConversation(history).execute(_REF)
