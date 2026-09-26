"""Testes de `CheckpointerConversationHistory` contra um saver dublê."""

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.modules.agent.adapters.redis.conversation_history import (
    CheckpointerConversationHistory,
)
from app.modules.agent.domain.entities import Channel, ConversationRef
from app.modules.agent.domain.exceptions import ConversationStateError

_REF = ConversationRef(Channel.TELEGRAM, "42")


class _StubSaver:
    """O mínimo do checkpointer que o adapter usa: apagar uma thread."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error
        self.deleted: list[str] = []

    async def adelete_thread(self, thread_id: str) -> None:
        if self._error is not None:
            raise self._error
        self.deleted.append(thread_id)


async def test_apaga_a_thread_no_checkpointer() -> None:
    saver = _StubSaver()

    await CheckpointerConversationHistory(saver).clear(_REF)  # type: ignore[arg-type]

    assert saver.deleted == ["telegram:42"]


async def test_falha_de_redis_vira_conversation_state_error() -> None:
    saver = _StubSaver(error=RedisConnectionError("Redis recusou a conexão"))

    with pytest.raises(ConversationStateError):
        await CheckpointerConversationHistory(saver).clear(_REF)  # type: ignore[arg-type]
