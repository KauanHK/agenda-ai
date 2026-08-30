"""Poda do histórico antes de chamar o modelo.

Uma thread longa estoura a janela de contexto e o custo por turno. Função pura,
testável isolada: a regra que importa é nunca separar um `AIMessage` que pediu
tools dos `ToolMessage` que respondem a ele — a API do provider rejeita a
requisição se um `tool_call` fica sem resultado ou um resultado sem a chamada.
"""

from langchain_core.messages import AnyMessage, ToolMessage


def trim_history(messages: list[AnyMessage], limit: int) -> list[AnyMessage]:
    """Mantém as últimas `limit` mensagens sem quebrar pares de tool call/resultado.

    Se a janela começaria num `ToolMessage` — órfão do `AIMessage` que o pediu —,
    ela recua até incluir esse `AIMessage`. O resultado pode passar de `limit`
    por algumas mensagens; a integridade dos pares vale mais que o teto exato.
    """
    if limit <= 0 or len(messages) <= limit:
        return list(messages)

    start = len(messages) - limit
    while start > 0 and isinstance(messages[start], ToolMessage):
        start -= 1
    return list(messages[start:])
