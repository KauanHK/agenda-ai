"""Adapter de `ConversationHistoryProtocol` sobre o checkpointer do LangGraph.

Ao contrário do cache de sessão, uma falha de Redis aqui **não** é engolida:
não conseguir apagar o histórico deixa o cliente achando que recomeçou do zero
quando não recomeçou, então vira `ConversationStateError` — o mesmo tratamento
que o `runner` dá a uma falha de leitura/escrita do checkpointer.
"""

import logging
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from redis.exceptions import RedisError

from src.domain.entities import ConversationRef
from src.domain.exceptions import ConversationStateError

logger = logging.getLogger(__name__)


class CheckpointerConversationHistory:
    """Apaga os checkpoints de uma thread. Implementa `ConversationHistoryProtocol`."""

    def __init__(self, saver: BaseCheckpointSaver[Any]) -> None:
        self._saver = saver

    async def clear(self, conversation: ConversationRef) -> None:
        """Apaga o histórico da thread; apagar uma que não existe não é erro."""
        try:
            await self._saver.adelete_thread(conversation.thread_id)
        except RedisError as exc:
            logger.warning("Falha ao apagar o histórico da thread %s", conversation.thread_id)
            raise ConversationStateError(
                "Não foi possível apagar o histórico da conversa."
            ) from exc
