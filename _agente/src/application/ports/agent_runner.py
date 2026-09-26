"""Porta de execução de um turno do agente sobre o histórico da conversa."""

from collections.abc import Sequence
from typing import Any, Protocol

from src.domain.entities import AgentAnswer, AgentContext, ConversationRef


class AgentRunnerProtocol(Protocol):
    """Roda um turno do agente e devolve o texto final da resposta.

    O que orquestra o turno — grafo, modelo, ciclo de tools — é detalhe de
    implementação. A aplicação só entrega a conversa, o texto do cliente, as
    tools da sessão e o contexto, e recebe de volta o que responder.
    """

    async def run(
        self,
        *,
        conversation: ConversationRef,
        user_text: str,
        tools: Sequence[Any],
        context: AgentContext,
    ) -> AgentAnswer:
        """Roda um turno do agente sobre o histórico da conversa.

        O tipo de cada tool é opaco aqui (`Any`), como em
        `BookingToolProviderProtocol`: quem as entende é o runner.

        Raises:
            AgentUnavailableError: Se o modelo falhar, estourar o tempo ou o
                teto de passos do grafo.
            ConversationStateError: Se o histórico não puder ser lido ou gravado.
        """
        ...
