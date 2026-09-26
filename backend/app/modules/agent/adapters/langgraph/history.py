"""Poda do histórico antes de chamar o modelo.

Uma thread longa estoura a janela de contexto e o custo por turno. Função pura,
testável isolada. A unidade da poda é o **turno** — um `HumanMessage` e tudo que
o agente produziu em resposta (tool calls, resultados, resposta final) —, não a
mensagem: um único turno com várias consultas de agenda gera dez ou mais
mensagens, e contar mensagens deixaria o modelo ver os resultados das tools sem
a pergunta que os motivou. Cortar no `HumanMessage` também garante que nenhum
`AIMessage` que pediu tools fica separado dos `ToolMessage` que o respondem — a
API do provider rejeita a requisição se um `tool_call` fica sem resultado ou um
resultado sem a chamada.
"""

from langchain_core.messages import AnyMessage, HumanMessage


def trim_history(messages: list[AnyMessage], limit: int) -> list[AnyMessage]:
    """Mantém os últimos `limit` turnos: cada `HumanMessage` e tudo que vem depois dele.

    Com `limit <= 0` não corta. O turno atual conta como um dos `limit`.
    """
    if limit <= 0:
        return list(messages)

    remaining = limit
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            remaining -= 1
            if remaining == 0:
                return list(messages[index:])
    return list(messages)


def is_first_turn(messages: list[AnyMessage]) -> bool:
    """Verdadeiro se o histórico só tem o `HumanMessage` do turno atual."""
    return sum(isinstance(message, HumanMessage) for message in messages) <= 1
