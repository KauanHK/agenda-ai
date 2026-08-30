"""O runner: a única classe de `infrastructure/agent` que a aplicação enxerga.

Implementa `AgentRunnerProtocol` sobre um grafo já compilado. Monta o `config`
do turno, dirige o grafo, extrai o texto do último `AIMessage`, conta as tool
calls e traduz as falhas do LangGraph/LLM/checkpointer em erros do domínio.
"""

import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError
from redis.exceptions import RedisError

from src.domain.entities import AgentAnswer, AgentContext, ConversationRef
from src.domain.exceptions import AgentUnavailableError, ConversationStateError
from src.infrastructure.agent.graph import CompiledConversationGraph

logger = logging.getLogger(__name__)

_FALLBACK_TEXT = "Certo! Posso ajudar em mais alguma coisa?"


class LangGraphAgentRunner:
    """Roda um turno do agente sobre um grafo compilado. Implementa `AgentRunnerProtocol`."""

    def __init__(
        self,
        graph: CompiledConversationGraph,
        *,
        max_agent_steps: int,
        fallback_text: str = _FALLBACK_TEXT,
    ) -> None:
        self._graph = graph
        # Cada passo do agente é um par call_model → call_tools; +1 pela chamada final.
        self._recursion_limit = max_agent_steps * 2 + 1
        self._fallback_text = fallback_text

    async def run(
        self,
        *,
        conversation: ConversationRef,
        user_text: str,
        tools: Sequence[Any],
        context: AgentContext,
    ) -> AgentAnswer:
        """Roda um turno e devolve o texto final, com a contagem de tool calls."""
        config = self._build_config(conversation, tools, context)
        last_answer, tool_calls_made = await self._drive(user_text, config)

        text = last_answer.text.strip() if last_answer is not None else ""
        if not text:
            logger.info("Turno de %s terminou sem texto; usando fallback", conversation.thread_id)
        return AgentAnswer(text=text or self._fallback_text, tool_calls_made=tool_calls_made)

    def _build_config(
        self,
        conversation: ConversationRef,
        tools: Sequence[Any],
        context: AgentContext,
    ) -> RunnableConfig:
        """Injeta o contexto do turno em `configurable` e o teto de passos do grafo."""
        return {
            "configurable": {
                "thread_id": conversation.thread_id,
                "tools": list(tools),
                "client_name": context.client_name,
                "now": context.now,
                "is_new_client": context.is_new_client,
            },
            "recursion_limit": self._recursion_limit,
        }

    async def _drive(
        self,
        user_text: str,
        config: RunnableConfig,
    ) -> tuple[AIMessage | None, int]:
        """Consome o stream do grafo, guardando a última resposta e contando as tools."""
        last_answer: AIMessage | None = None
        tool_calls_made = 0
        turn_input = {"messages": [HumanMessage(user_text)]}
        try:
            async for update in self._graph.astream(turn_input, config, stream_mode="updates"):
                for node, payload in update.items():
                    messages = payload.get("messages", []) if isinstance(payload, dict) else []
                    if node == "call_tools":
                        tool_calls_made += len(messages)
                    elif node == "call_model" and messages and isinstance(messages[-1], AIMessage):
                        last_answer = messages[-1]
        except GraphRecursionError as exc:
            raise AgentUnavailableError("O agente excedeu o número de passos do turno.") from exc
        except RedisError as exc:
            raise ConversationStateError("Falha ao ler ou gravar o histórico da conversa.") from exc
        except AgentUnavailableError, ConversationStateError:
            raise
        except Exception as exc:
            # Toda falha restante do LLM ou do grafo vira erro de domínio.
            raise AgentUnavailableError("O modelo falhou ao responder o turno.") from exc
        return last_answer, tool_calls_made
