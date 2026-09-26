"""`FakeChatModel`: um chat model roteirizado para os testes do grafo.

Nenhum teste automático chama a API de um provider. As respostas são uma lista de
`AIMessage` consumida em ordem; esgotada a lista, o último item se repete (útil
para simular um loop de tool calls que estoura o `recursion_limit`).

Cada resposta é **copiada** a cada invocação: o reducer `add_messages` deduplica
por `id` e reaproveitar a mesma instância faria o grafo parar sozinho.
"""

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from pydantic import Field


class FakeChatModel(BaseChatModel):
    """Chat model de teste: devolve `AIMessage`s roteirizados e registra o que recebeu."""

    responses: list[AIMessage]
    index: int = 0
    received: list[list[BaseMessage]] = Field(default_factory=list)
    bound_tools: list[Any] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"

    def _next(self, messages: list[BaseMessage]) -> AIMessage:
        self.received.append(list(messages))
        template = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return template.model_copy(update={"id": None})

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next(messages))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._next(messages))])

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        self.bound_tools = list(tools)
        return self
