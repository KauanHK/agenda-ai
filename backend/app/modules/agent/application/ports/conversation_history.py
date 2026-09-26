"""Porta de gestão do histórico durável de uma conversa."""

from typing import Protocol

from app.modules.agent.domain.entities import ConversationRef


class ConversationHistoryProtocol(Protocol):
    """Opera sobre o histórico persistido de uma conversa sem conhecer o checkpointer.

    Existe para que o caso de uso `ResetConversation` possa descartar o histórico
    sem importar LangGraph nem Redis. Muda quando o backend de checkpoint muda —
    motivo diferente de `AgentRunnerProtocol`, que muda quando a orquestração do
    turno muda.
    """

    async def clear(self, conversation: ConversationRef) -> None:
        """Descarta o histórico persistido da conversa.

        Idempotente: apagar uma conversa que não existe (ou já expirou) não é
        erro.

        Raises:
            ConversationStateError: Se o histórico não puder ser apagado.
        """
        ...
