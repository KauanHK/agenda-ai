"""Testes de `LangGraphAgentRunner`: extração da resposta, contagem e erros."""

from datetime import UTC, datetime
from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from redis.exceptions import ConnectionError as RedisConnectionError

from src.domain.entities import AgentContext, Channel, ConversationRef
from src.domain.exceptions import AgentUnavailableError, ConversationStateError
from src.infrastructure.agent.graph import build_graph
from src.infrastructure.agent.runner import LangGraphAgentRunner
from tests.fakes.chat_model import FakeChatModel

_REF = ConversationRef(Channel.TELEGRAM, "999")


def _context() -> AgentContext:
    return AgentContext(
        client_name="Kauan",
        now=datetime(2026, 8, 28, 10, 0, tzinfo=UTC),
        is_new_client=False,
    )


@tool
async def list_services() -> str:
    """Lista os serviços."""
    return '{"success": true, "data": [{"name": "Corte"}]}'


def _tool_call(name: str, call_id: str) -> dict[str, Any]:
    return {"name": name, "args": {}, "id": call_id, "type": "tool_call"}


def _runner(
    model: FakeChatModel,
    *,
    checkpointer: Any = None,
    max_agent_steps: int = 8,
) -> LangGraphAgentRunner:
    graph = build_graph(
        model,
        checkpointer=checkpointer or InMemorySaver(),
        history_limit=40,
    )
    return LangGraphAgentRunner(graph, max_agent_steps=max_agent_steps)


async def test_caminho_feliz_extrai_o_texto_final_e_conta_as_tool_calls() -> None:
    model = FakeChatModel(
        responses=[
            AIMessage(content="", tool_calls=[_tool_call("list_services", "c1")]),
            AIMessage("Temos Corte. Quer marcar?"),
        ]
    )

    answer = await _runner(model).run(
        conversation=_REF,
        user_text="que serviços vocês têm?",
        tools=[list_services],
        context=_context(),
    )

    assert answer.text == "Temos Corte. Quer marcar?"
    assert answer.tool_calls_made == 1


async def test_resposta_final_vazia_vira_frase_de_fallback() -> None:
    model = FakeChatModel(
        responses=[
            AIMessage(content="", tool_calls=[_tool_call("list_services", "c1")]),
            AIMessage(""),
        ]
    )

    answer = await _runner(model).run(
        conversation=_REF,
        user_text="oi",
        tools=[list_services],
        context=_context(),
    )

    assert answer.text
    assert answer.tool_calls_made == 1


async def test_estouro_do_recursion_limit_vira_agent_unavailable() -> None:
    # Sempre pede a mesma tool: o ciclo nunca termina até o teto de passos.
    model = FakeChatModel(
        responses=[AIMessage(content="", tool_calls=[_tool_call("list_services", "c")])]
    )

    with pytest.raises(AgentUnavailableError):
        await _runner(model, max_agent_steps=3).run(
            conversation=_REF,
            user_text="oi",
            tools=[list_services],
            context=_context(),
        )


async def test_falha_do_modelo_vira_agent_unavailable() -> None:
    class BoomModel(FakeChatModel):
        async def _agenerate(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("provider fora do ar")

    model = BoomModel(responses=[AIMessage("nunca chega")])

    with pytest.raises(AgentUnavailableError):
        await _runner(model).run(
            conversation=_REF,
            user_text="oi",
            tools=[list_services],
            context=_context(),
        )


async def test_falha_do_checkpointer_vira_conversation_state_error() -> None:
    class BrokenSaver(InMemorySaver):
        async def aget_tuple(self, config: Any) -> Any:
            raise RedisConnectionError("Redis recusou a conexão")

    model = FakeChatModel(responses=[AIMessage("olá")])

    with pytest.raises(ConversationStateError):
        await _runner(model, checkpointer=BrokenSaver()).run(
            conversation=_REF,
            user_text="oi",
            tools=[list_services],
            context=_context(),
        )


async def test_historico_persiste_entre_turnos_na_mesma_thread() -> None:
    checkpointer = InMemorySaver()

    first = FakeChatModel(responses=[AIMessage("oi, quem fala?")])
    await _runner(first, checkpointer=checkpointer).run(
        conversation=_REF,
        user_text="bom dia",
        tools=[],
        context=_context(),
    )

    second = FakeChatModel(responses=[AIMessage("claro!")])
    await _runner(second, checkpointer=checkpointer).run(
        conversation=_REF,
        user_text="pode me ajudar?",
        tools=[],
        context=_context(),
    )

    # O segundo turno recebeu o histórico do primeiro no prompt.
    sent = second.received[0]
    assert any("bom dia" in str(m.content) for m in sent)
    assert any("oi, quem fala?" in str(m.content) for m in sent)
