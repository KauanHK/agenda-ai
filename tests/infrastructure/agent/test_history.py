"""Testes de `trim_history`: teto de mensagens sem quebrar pares tool call/resultado."""

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage

from src.infrastructure.agent.history import trim_history


def _turn(n: int) -> list[AnyMessage]:
    """Um par pergunta/resposta simples, numerado."""
    return [HumanMessage(f"pergunta {n}"), AIMessage(f"resposta {n}")]


def test_devolve_tudo_quando_esta_abaixo_do_limite() -> None:
    messages = [*_turn(1), *_turn(2)]

    assert trim_history(messages, 10) == messages


def test_devolve_uma_lista_nova_e_nao_a_original() -> None:
    messages = _turn(1)

    result = trim_history(messages, 10)

    assert result == messages
    assert result is not messages


def test_corta_para_as_ultimas_mensagens_quando_passa_do_limite() -> None:
    messages = [*_turn(1), *_turn(2), *_turn(3)]

    result = trim_history(messages, 2)

    assert result == _turn(3)


def test_limite_zero_ou_negativo_nao_corta() -> None:
    messages = [*_turn(1), *_turn(2)]

    assert trim_history(messages, 0) == messages
    assert trim_history(messages, -5) == messages


def test_nunca_comeca_por_um_tool_message_orfao() -> None:
    ai_with_calls = AIMessage(
        content="",
        tool_calls=[{"name": "t", "args": {}, "id": "c1", "type": "tool_call"}],
    )
    messages: list[AnyMessage] = [
        HumanMessage("marca aí"),
        ai_with_calls,
        ToolMessage(content="{}", tool_call_id="c1"),
        AIMessage("marquei"),
    ]

    # limite 2 pegaria [ToolMessage, AIMessage] — o ToolMessage ficaria sem a chamada.
    result = trim_history(messages, 2)

    assert result[0] is ai_with_calls
    assert result == messages[1:]


def test_recua_sobre_varios_tool_messages_do_mesmo_lote() -> None:
    ai_with_calls = AIMessage(
        content="",
        tool_calls=[
            {"name": "a", "args": {}, "id": "c1", "type": "tool_call"},
            {"name": "b", "args": {}, "id": "c2", "type": "tool_call"},
        ],
    )
    messages: list[AnyMessage] = [
        HumanMessage("oi"),
        ai_with_calls,
        ToolMessage(content="{}", tool_call_id="c1"),
        ToolMessage(content="{}", tool_call_id="c2"),
        AIMessage("pronto"),
    ]

    result = trim_history(messages, 2)

    assert result[0] is ai_with_calls
