"""Fake de `AgentRunnerProtocol` para os testes de aplicação."""

from collections.abc import Sequence
from typing import Any

from src.domain.entities import AgentAnswer, AgentContext, ConversationRef
from src.domain.exceptions import AgentError


class FakeAgentRunner:
    """Devolve uma resposta roteirizada (ou levanta) e registra cada turno."""

    def __init__(
        self,
        answer: AgentAnswer | None = None,
        *,
        error: AgentError | None = None,
    ) -> None:
        self._answer = answer or AgentAnswer(text="ok", tool_calls_made=0)
        self._error = error
        self.calls: list[tuple[ConversationRef, str, Sequence[Any], AgentContext]] = []

    async def run(
        self,
        *,
        conversation: ConversationRef,
        user_text: str,
        tools: Sequence[Any],
        context: AgentContext,
    ) -> AgentAnswer:
        self.calls.append((conversation, user_text, tools, context))
        if self._error is not None:
            raise self._error
        return self._answer
