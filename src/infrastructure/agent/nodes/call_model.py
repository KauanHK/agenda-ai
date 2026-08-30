"""Nó `call_model`: pede a próxima ação ao LLM, já com as tools da sessão."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.infrastructure.agent.history import trim_history
from src.infrastructure.agent.prompts import (
    PromptContext,
    render_system_prompt,
    render_turn_context,
)
from src.infrastructure.agent.state import ConversationState, load_turn_config


async def call_model(
    state: ConversationState,
    config: RunnableConfig,
    *,
    model: BaseChatModel,
    history_limit: int,
) -> dict[str, list[AnyMessage]]:
    """Renderiza o system prompt, vincula as tools do turno e chama o modelo.

    O modelo e o limite de histórico vêm fechados na montagem do grafo; as tools
    e o contexto do cliente vêm em `config["configurable"]`. O nó não conhece
    provider nem env.

    O prompt sai em duas mensagens: a estática (`render_system_prompt`), que é o
    mesmo texto para todo turno e serve de prefixo de cache, e o contexto volátil
    do turno (`render_turn_context`), numa segunda `SystemMessage` fora do bloco
    cacheável.
    """
    turn = load_turn_config(config)
    context = PromptContext(
        client_name=turn["client_name"],
        now=turn["now"],
        is_new_client=turn["is_new_client"],
    )
    system = SystemMessage(render_system_prompt())
    turn_context = SystemMessage(render_turn_context(context))
    history = trim_history(state["messages"], history_limit)
    answer = await model.bind_tools(turn["tools"]).ainvoke([system, turn_context, *history], config)
    return {"messages": [answer]}
