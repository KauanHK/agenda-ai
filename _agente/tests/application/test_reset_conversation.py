"""Testes de `ResetConversation`: apaga a thread certa e propaga a falha do Redis."""

import pytest

from src.application.use_cases.reset_conversation import ResetConversation
from src.domain.entities import Channel, ConversationRef
from src.domain.exceptions import ConversationStateError
from tests.fakes.conversation_history import FakeConversationHistory

_REF = ConversationRef(Channel.TELEGRAM, "42")


async def test_apaga_o_historico_da_conversa() -> None:
    history = FakeConversationHistory()

    await ResetConversation(history).execute(_REF)

    assert history.cleared == [_REF]


async def test_propaga_a_falha_ao_apagar_o_historico() -> None:
    history = FakeConversationHistory(error=ConversationStateError("Redis recusou"))

    with pytest.raises(ConversationStateError):
        await ResetConversation(history).execute(_REF)
