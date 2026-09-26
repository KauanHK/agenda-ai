"""Testes de `render_system_prompt` (estático) e `render_turn_context` (volátil)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.agent.adapters.langgraph.prompts import (
    PromptContext,
    render_system_prompt,
    render_turn_context,
)

_SP = ZoneInfo("America/Sao_Paulo")


def _context(*, is_new_client: bool = False, now: datetime | None = None) -> PromptContext:
    return PromptContext(
        client_name="Kauan",
        now=now or datetime(2026, 8, 28, 14, 30, tzinfo=_SP),
        is_new_client=is_new_client,
    )


class TestSystemPrompt:
    def test_nao_depende_do_turno(self) -> None:
        # Mesmo texto para todo cliente e toda invocação: é o prefixo cacheável.
        assert render_system_prompt() == render_system_prompt()

    def test_nao_carrega_dados_do_cliente(self) -> None:
        prompt = render_system_prompt()

        assert "Kauan" not in prompt
        assert "Contexto do turno" not in prompt

    def test_traz_as_regras_de_agenda_essenciais(self) -> None:
        prompt = render_system_prompt()

        assert "list_available_slots" in prompt
        assert "create_scheduling" in prompt
        assert "reschedule_scheduling" in prompt

    def test_proibe_expor_termos_internos_ao_cliente(self) -> None:
        prompt = render_system_prompt()

        assert "UUID" in prompt
        assert "MCP" in prompt


class TestTurnContext:
    def test_inclui_o_nome_do_cliente(self) -> None:
        assert "Kauan" in render_turn_context(_context())

    def test_inclui_dia_da_semana_data_e_hora_em_pt_br(self) -> None:
        # 28/08/2026 é uma sexta-feira.
        block = render_turn_context(_context(now=datetime(2026, 8, 28, 14, 30, tzinfo=_SP)))

        assert "sexta-feira" in block
        assert "28/08/2026" in block
        assert "14:30" in block

    def test_marca_o_primeiro_contato_do_cliente(self) -> None:
        novo = render_turn_context(_context(is_new_client=True))
        conhecido = render_turn_context(_context(is_new_client=False))

        assert "primeiro contato" in novo
        assert "primeiro contato" not in conhecido
