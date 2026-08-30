"""Testes de `render_system_prompt`: contexto do turno e regras de agenda."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.infrastructure.agent.prompts import PromptContext, render_system_prompt

_SP = ZoneInfo("America/Sao_Paulo")


def _context(*, is_new_client: bool = False, now: datetime | None = None) -> PromptContext:
    return PromptContext(
        client_name="Kauan",
        now=now or datetime(2026, 8, 28, 14, 30, tzinfo=_SP),
        is_new_client=is_new_client,
    )


def test_inclui_o_nome_do_cliente() -> None:
    assert "Kauan" in render_system_prompt(_context())


def test_inclui_dia_da_semana_data_e_hora_em_pt_br() -> None:
    # 28/08/2026 é uma sexta-feira.
    prompt = render_system_prompt(_context(now=datetime(2026, 8, 28, 14, 30, tzinfo=_SP)))

    assert "sexta-feira" in prompt
    assert "28/08/2026" in prompt
    assert "14:30" in prompt


def test_marca_o_primeiro_contato_do_cliente() -> None:
    novo = render_system_prompt(_context(is_new_client=True))
    conhecido = render_system_prompt(_context(is_new_client=False))

    assert "primeiro contato" in novo
    assert "primeiro contato" not in conhecido


def test_traz_as_regras_de_agenda_essenciais() -> None:
    prompt = render_system_prompt(_context())

    assert "list_available_slots" in prompt
    assert "create_scheduling" in prompt
    assert "reschedule_scheduling" in prompt


def test_proibe_expor_termos_internos_ao_cliente() -> None:
    prompt = render_system_prompt(_context())

    assert "UUID" in prompt
    assert "MCP" in prompt
