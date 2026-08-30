"""Nó `call_tools`: executa as tool calls pedidas pelo modelo.

Um `ToolNode` do LangGraph não serve: ele recebe as tools na construção do grafo,
e aqui elas chegam autenticadas por sessão a cada turno, em `configurable`. Uma
tool inexistente ou que levanta exceção vira um `ToolMessage` de erro — a falha
volta para o modelo em vez de derrubar o turno.
"""

import asyncio
import json

from langchain_core.messages import AIMessage, AnyMessage, ToolCall, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from src.infrastructure.agent.state import ConversationState, load_turn_config


async def call_tools(
    state: ConversationState,
    config: RunnableConfig,
) -> dict[str, list[AnyMessage]]:
    """Roda em paralelo as tool calls da última mensagem e devolve os resultados."""
    tools_by_name = {tool.name: tool for tool in load_turn_config(config)["tools"]}
    last = state["messages"][-1]
    tool_calls = last.tool_calls if isinstance(last, AIMessage) else []

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(_invoke(tools_by_name=tools_by_name, call=call, config=config))
            for call in tool_calls
        ]
    results: list[AnyMessage] = [task.result() for task in tasks]
    return {"messages": results}


async def _invoke(
    tools_by_name: dict[str, BaseTool],
    call: ToolCall,
    config: RunnableConfig,
) -> ToolMessage:
    """Executa uma tool call, traduzindo ausência e exceção em `ToolMessage` de erro."""
    tool = tools_by_name.get(call["name"])
    if tool is None:
        return _failure(call, f"tool desconhecida: {call['name']}")
    try:
        result = await tool.ainvoke(call, config)
    except Exception as exc:
        # A falha da tool volta ao modelo como resultado, não derruba o turno.
        return _failure(call, str(exc))
    return _as_tool_message(call, result)


def _as_tool_message(call: ToolCall, result: object) -> ToolMessage:
    """Normaliza o retorno da tool: já é `ToolMessage` ou vira conteúdo de texto."""
    if isinstance(result, ToolMessage):
        return result
    return ToolMessage(
        content=str(result),
        tool_call_id=call["id"] or "",
        name=call["name"],
    )


def _failure(call: ToolCall, reason: str) -> ToolMessage:
    """Envelope de erro no mesmo formato das tools, para o modelo decidir o próximo passo."""
    envelope = {"success": False, "error_code": "tool_failed", "message": reason}
    return ToolMessage(
        content=json.dumps(envelope, ensure_ascii=False),
        tool_call_id=call["id"] or "",
        name=call["name"],
        status="error",
    )
