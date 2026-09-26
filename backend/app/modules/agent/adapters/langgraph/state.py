"""O estado persistido por thread e o contexto injetado a cada turno.

`ConversationState` é tudo que o checkpointer grava; `TurnConfig` é tudo que
varia por invocação e **não** deve ser persistido — as tools são autenticadas
por uma sessão de minutos, e guardar isso no histórico durável seria manter
credencial expirada.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """O que o checkpointer persiste por thread."""

    messages: Annotated[list[AnyMessage], add_messages]


class TurnConfig(TypedDict):
    """O contexto do turno, lido de `config["configurable"]` pelos nós."""

    thread_id: str
    tools: Sequence[BaseTool]
    client_name: str
    now: datetime
    is_new_client: bool


def load_turn_config(config: RunnableConfig) -> TurnConfig:
    """Extrai o `TurnConfig` de um `RunnableConfig`, exigindo todas as chaves."""
    configurable: dict[str, Any] = config.get("configurable", {})
    return TurnConfig(
        thread_id=configurable["thread_id"],
        tools=configurable["tools"],
        client_name=configurable["client_name"],
        now=configurable["now"],
        is_new_client=configurable["is_new_client"],
    )
