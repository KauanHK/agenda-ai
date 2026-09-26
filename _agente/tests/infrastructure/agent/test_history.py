"""Testes de `trim_history` e `is_first_turn`: poda por turno, nunca por mensagem."""

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage

from src.infrastructure.agent.history import is_first_turn, trim_history


def _turn(n: int) -> list[AnyMessage]:
    """Um par pergunta/resposta simples, numerado."""
    return [HumanMessage(f"pergunta {n}"), AIMessage(f"resposta {n}")]


def _turn_with_tools(n: int, calls: int) -> list[AnyMessage]:
    """Um turno que fez `calls` tool calls em sequência antes de responder."""
    messages: list[AnyMessage] = [HumanMessage(f"pergunta {n}")]
    for i in range(calls):
        call_id = f"c{n}-{i}"
        messages.append(
            AIMessage(
                content="",
                tool_calls=[{"name": "t", "args": {}, "id": call_id, "type": "tool_call"}],
            )
        )
        messages.append(ToolMessage(content="{}", tool_call_id=call_id))
    messages.append(AIMessage(f"resposta {n}"))
    return messages


class TestTrimHistory:
    def test_devolve_tudo_quando_esta_abaixo_do_limite(self) -> None:
        messages = [*_turn(1), *_turn(2)]

        assert trim_history(messages, 10) == messages

    def test_devolve_uma_lista_nova_e_nao_a_original(self) -> None:
        messages = _turn(1)

        result = trim_history(messages, 10)

        assert result == messages
        assert result is not messages

    def test_corta_para_os_ultimos_turnos_quando_passa_do_limite(self) -> None:
        messages = [*_turn(1), *_turn(2), *_turn(3)]

        result = trim_history(messages, 2)

        assert result == [*_turn(2), *_turn(3)]

    def test_limite_zero_ou_negativo_nao_corta(self) -> None:
        messages = [*_turn(1), *_turn(2)]

        assert trim_history(messages, 0) == messages
        assert trim_history(messages, -5) == messages

    def test_um_turno_com_muitas_tool_calls_nao_engole_a_janela(self) -> None:
        # Contando mensagens, o turno 1 (10 mensagens) sozinho passaria do limite
        # e o modelo veria os resultados das tools sem a pergunta que os motivou.
        turn_1 = _turn_with_tools(1, calls=4)
        turn_2 = [HumanMessage("pergunta 2")]
        messages = [*turn_1, *turn_2]

        result = trim_history(messages, 2)

        assert result == messages
        assert isinstance(result[0], HumanMessage)

    def test_o_turno_atual_conta_como_um_dos_limite(self) -> None:
        messages = [*_turn(1), *_turn(2), HumanMessage("pergunta 3")]

        result = trim_history(messages, 1)

        assert result == [HumanMessage("pergunta 3")]

    def test_sempre_comeca_por_um_human_message(self) -> None:
        messages = [*_turn_with_tools(1, calls=2), *_turn_with_tools(2, calls=3)]

        result = trim_history(messages, 1)

        assert result == _turn_with_tools(2, calls=3)
        assert not any(isinstance(m, ToolMessage) for m in result[:1])


class TestIsFirstTurn:
    def test_verdadeiro_com_so_a_mensagem_do_turno_atual(self) -> None:
        assert is_first_turn([HumanMessage("oi")]) is True

    def test_verdadeiro_com_historico_vazio(self) -> None:
        assert is_first_turn([]) is True

    def test_falso_a_partir_do_segundo_turno(self) -> None:
        assert is_first_turn([*_turn(1), HumanMessage("de novo")]) is False

    def test_tool_messages_do_turno_atual_nao_contam_como_turno(self) -> None:
        assert is_first_turn(_turn_with_tools(1, calls=3)) is True
