"""Montagem e compilação do grafo.

O ciclo ReAct escrito à mão, em vez de `create_react_agent`: as tools mudam a
cada turno (vêm autenticadas por sessão) e o `bind` precisa acontecer dentro da
execução, não na construção. O grafo é montado **uma vez** no startup e compilado
com o checkpointer; só os dados variam por turno, via `config["configurable"]`.
"""

import functools
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.infrastructure.agent.nodes.call_model import call_model
from src.infrastructure.agent.nodes.call_tools import call_tools
from src.infrastructure.agent.state import ConversationState

CompiledConversationGraph = CompiledStateGraph[ConversationState, Any, Any, Any]


def should_continue(state: ConversationState) -> Literal["call_tools", "__end__"]:
    """Continua em tools enquanto a última mensagem pedir tool calls; senão, termina.

    O `"__end__"` do retorno é o valor de `langgraph.graph.END`.
    """
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "call_tools"
    return "__end__"


def build_graph(
    model: BaseChatModel,
    *,
    checkpointer: BaseCheckpointSaver[Any],
    history_limit: int,
) -> CompiledConversationGraph:
    """Monta o grafo `call_model ⇄ call_tools` e o compila com o checkpointer."""
    bound_call_model = functools.partial(call_model, model=model, history_limit=history_limit)

    builder: StateGraph[ConversationState, Any, Any, Any] = StateGraph(ConversationState)
    builder.add_node("call_model", bound_call_model)
    builder.add_node("call_tools", call_tools)
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", should_continue)
    builder.add_edge("call_tools", "call_model")

    return builder.compile(checkpointer=checkpointer)
