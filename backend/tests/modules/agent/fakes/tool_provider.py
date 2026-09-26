"""Fakes de `BookingToolProviderProtocol` para os testes de aplicação."""

from collections.abc import Sequence
from typing import Any

from app.modules.agent.domain.exceptions import AgentError


class FakeToolProvider:
    """Devolve uma lista roteirizada de tools (ou levanta) e registra os tokens."""

    def __init__(
        self,
        tools: Sequence[Any] | None = None,
        *,
        error: AgentError | None = None,
    ) -> None:
        self._tools = list(tools or [])
        self._error = error
        self.tokens: list[str] = []

    async def tools_for(self, session_token: str) -> Sequence[Any]:
        self.tokens.append(session_token)
        if self._error is not None:
            raise self._error
        return self._tools
