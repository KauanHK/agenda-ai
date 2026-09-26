"""Testes de `match_command`."""

import pytest

from app.modules.agent.adapters.telegram.commands import match_command


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("/start", "start"),
        ("/reset", "reset"),
        ("/Start", "start"),
        ("/reset argumento ignorado", "reset"),
        ("/start@agenda_bot", "start"),
        ("  /reset  ", "reset"),
        ("/ajuda", "ajuda"),
    ],
)
def test_extrai_o_nome_do_comando(text: str, expected: str) -> None:
    assert match_command(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "oi, tudo bem?",
        "quero marcar às 15h",
        "e/mail no meio da frase",
        "",
        "/",
        "/ start com espaço depois da barra",
    ],
)
def test_texto_que_nao_e_comando_vira_none(text: str) -> None:
    assert match_command(text) is None
