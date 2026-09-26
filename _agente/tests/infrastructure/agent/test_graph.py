"""Testes de `should_continue` e da montagem do grafo."""

from datetime import UTC, datetime

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.infrastructure.agent.graph import build_graph, should_continue
from src.infrastructure.agent.state import ConversationState
from tests.fakes.chat_model import FakeChatModel


def _state(*messages: AnyMessage) -> ConversationState:
    return {"messages": list(messages)}


class TestShouldContinue:
    def test_continua_em_tools_quando_a_ultima_mensagem_pede_tool_calls(self) -> None:
        last = AIMessage(
            content="",
            tool_calls=[{"name": "t", "args": {}, "id": "c1", "type": "tool_call"}],
        )

        assert should_continue(_state(HumanMessage("oi"), last)) == "call_tools"

    def test_termina_quando_a_ultima_mensagem_nao_tem_tool_calls(self) -> None:
        assert should_continue(_state(HumanMessage("oi"), AIMessage("pronto"))) == "__end__"

    def test_termina_quando_a_ultima_mensagem_nao_e_do_modelo(self) -> None:
        last = ToolMessage(content="{}", tool_call_id="c1")

        assert should_continue(_state(AIMessage("x"), last)) == "__end__"


async def test_build_graph_compila_um_grafo_invocavel() -> None:
    model = FakeChatModel(responses=[AIMessage("olá, tudo bem?")])
    graph = build_graph(model, checkpointer=InMemorySaver(), history_limit=10)

    result = await graph.ainvoke(
        {"messages": [HumanMessage("oi")]},
        {
            "configurable": {
                "thread_id": "telegram:1",
                "tools": [],
                "client_name": "Kauan",
                "now": datetime.now(UTC),
                "is_new_client": False,
            }
        },
    )

    assert result["messages"][-1].content == "olá, tudo bem?"
