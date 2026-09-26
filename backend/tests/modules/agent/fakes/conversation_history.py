"""Fakes de `ConversationHistoryProtocol` para os testes de aplicação."""

from app.modules.agent.domain.entities import ConversationRef
from app.modules.agent.domain.exceptions import ConversationStateError


class FakeConversationHistory:
    """Registra as conversas apagadas; pode levantar sob demanda."""

    def __init__(self, *, error: ConversationStateError | None = None) -> None:
        self._error = error
        self.cleared: list[ConversationRef] = []

    async def clear(self, conversation: ConversationRef) -> None:
        if self._error is not None:
            raise self._error
        self.cleared.append(conversation)
