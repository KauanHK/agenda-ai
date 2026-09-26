"""Caso de uso: descartar o histórico de uma conversa, começando do zero.

Atende os comandos `/reset` e `/start` do canal. Apaga só o histórico
persistido da thread; não toca no cache do token de sessão nem em nada no
AgendaBot.
"""

from app.modules.agent.application.ports.conversation_history import (
    ConversationHistoryProtocol,
)
from app.modules.agent.domain.entities import ConversationRef


class ResetConversation:
    """Descarta o histórico persistido de uma conversa."""

    def __init__(self, history: ConversationHistoryProtocol) -> None:
        self._history = history

    async def execute(self, conversation: ConversationRef) -> None:
        """Apaga o histórico da conversa.

        Raises:
            ConversationStateError: Se o histórico não puder ser apagado.
        """
        await self._history.clear(conversation)
