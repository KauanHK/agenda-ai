"""Testes dos nós `call_model` e `call_tools`."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool

from src.infrastructure.agent.nodes.call_model import call_model
from src.infrastructure.agent.nodes.call_tools import call_tools
from src.infrastructure.agent.state import ConversationState
from tests.fakes.chat_model import FakeChatModel


@tool
async def list_services() -> str:
    """Lista os serviços."""
    return '{"success": true, "data": []}'


def _config(tools: list[BaseTool]) -> RunnableConfig:
    return {
        "configurable": {
            "thread_id": "telegram:1",
            "tools": tools,
            "client_name": "Kauan",
            "now": datetime(2026, 8, 28, 9, 0, tzinfo=UTC),
            "is_new_client": True,
        }
    }


def _state(*messages: AnyMessage) -> ConversationState:
    return {"messages": list(messages)}


class TestCallModel:
    async def test_chama_o_modelo_com_system_prompt_e_historico(self) -> None:
        model = FakeChatModel(responses=[AIMessage("olá")])

        result = await call_model(
            _state(HumanMessage("oi")),
            _config([list_services]),
            model=model,
            history_limit=10,
        )

        assert result["messages"][0].content == "olá"
        sent = model.received[0]
        assert isinstance(sent[0], SystemMessage)
        assert "Kauan" in sent[0].content
        assert isinstance(sent[1], HumanMessage)

    async def test_vincula_as_tools_do_turno(self) -> None:
        model = FakeChatModel(responses=[AIMessage("ok")])

        await call_model(
            _state(HumanMessage("oi")),
            _config([list_services]),
            model=model,
            history_limit=10,
        )

        assert model.bound_tools == [list_services]

    async def test_poda_o_historico_antes_de_chamar_o_modelo(self) -> None:
        model = FakeChatModel(responses=[AIMessage("ok")])
        history = [HumanMessage(f"msg {n}") for n in range(10)]

        await call_model(
            _state(*history),
            _config([list_services]),
            model=model,
            history_limit=3,
        )

        # 1 system + 3 do histórico podado.
        assert len(model.received[0]) == 4


class TestCallTools:
    async def test_executa_a_tool_e_casa_o_tool_call_id(self) -> None:
        call = {"name": "list_services", "args": {}, "id": "abc", "type": "tool_call"}
        state = _state(AIMessage(content="", tool_calls=[call]))

        result = await call_tools(state, _config([list_services]))

        message = result["messages"][0]
        assert isinstance(message, ToolMessage)
        assert message.tool_call_id == "abc"

    async def test_tool_inexistente_nao_derruba_o_turno(self) -> None:
        call = {"name": "nao_existe", "args": {}, "id": "x1", "type": "tool_call"}
        state = _state(AIMessage(content="", tool_calls=[call]))

        result = await call_tools(state, _config([list_services]))

        message = result["messages"][0]
        assert isinstance(message, ToolMessage)
        assert message.status == "error"
        assert '"success": false' in str(message.content)
        assert message.tool_call_id == "x1"

    async def test_excecao_na_tool_vira_tool_message_de_erro(self) -> None:
        @tool
        async def explode() -> str:
            """Sempre falha."""
            raise RuntimeError("backend caiu")

        call = {"name": "explode", "args": {}, "id": "e1", "type": "tool_call"}
        state = _state(AIMessage(content="", tool_calls=[call]))

        result = await call_tools(state, _config([explode]))

        message = result["messages"][0]
        assert message.status == "error"
        assert "tool_failed" in str(message.content)

    async def test_roda_as_tool_calls_em_paralelo(self) -> None:
        started = asyncio.Event()

        @tool
        async def waits() -> str:
            """Espera o sinal do par."""
            await asyncio.wait_for(started.wait(), timeout=1.0)
            return "liberou"

        @tool
        async def signals() -> str:
            """Libera o par."""
            started.set()
            return "sinalizou"

        calls: list[dict[str, Any]] = [
            {"name": "waits", "args": {}, "id": "w", "type": "tool_call"},
            {"name": "signals", "args": {}, "id": "s", "type": "tool_call"},
        ]
        state = _state(AIMessage(content="", tool_calls=calls))

        # Sequencial travaria: `waits` roda primeiro e nunca recebe o sinal.
        result = await asyncio.wait_for(
            call_tools(state, _config([waits, signals])),
            timeout=1.0,
        )

        ids = {m.tool_call_id for m in result["messages"]}
        assert ids == {"w", "s"}

    async def test_sem_tool_calls_devolve_lista_vazia(self) -> None:
        result = await call_tools(_state(AIMessage("só texto")), _config([list_services]))

        assert result["messages"] == []
