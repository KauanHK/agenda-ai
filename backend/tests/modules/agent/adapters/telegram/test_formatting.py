"""Testes das funções puras de `formatting.py`."""

from app.modules.agent.adapters.telegram.formatting import (
    TELEGRAM_MAX_CHARS,
    split_for_telegram,
    to_telegram_text,
)


def test_to_telegram_text_remove_negrito_e_titulos_e_colapsa_linhas() -> None:
    raw = "## Resumo\n\n\n\nTemos **corte** e **barba**.\n\n\n### Detalhes\nÀs 14h."

    assert to_telegram_text(raw) == "Resumo\n\nTemos corte e barba.\n\nDetalhes\nÀs 14h."


def test_to_telegram_text_nao_toca_em_texto_ja_limpo() -> None:
    raw = "Beleza, marquei pra amanhã às 14h. Te espero!"

    assert to_telegram_text(raw) == raw


def test_split_devolve_lista_vazia_para_texto_vazio() -> None:
    assert split_for_telegram("   ") == []


def test_split_mantem_texto_curto_num_pedaco_so() -> None:
    assert split_for_telegram("uma linha só") == ["uma linha só"]


def test_split_respeita_o_teto_e_nao_corta_palavra_no_meio() -> None:
    palavra = "agendamento"
    texto = " ".join([palavra] * 800)  # ~9600 chars

    pedacos = split_for_telegram(texto)

    assert len(pedacos) > 1
    assert all(len(pedaco) <= TELEGRAM_MAX_CHARS for pedaco in pedacos)
    for pedaco in pedacos:
        for token in pedaco.split():
            assert token == palavra
    assert " ".join(pedacos).split() == texto.split()


def test_split_quebra_entre_paragrafos_quando_possivel() -> None:
    paragrafo = "a" * 3000
    texto = f"{paragrafo}\n\n{paragrafo}"

    pedacos = split_for_telegram(texto)

    assert pedacos == [paragrafo, paragrafo]


def test_split_corta_palavra_gigante_sozinha() -> None:
    gigante = "x" * (TELEGRAM_MAX_CHARS + 500)

    pedacos = split_for_telegram(gigante)

    assert len(pedacos) == 2
    assert all(len(pedaco) <= TELEGRAM_MAX_CHARS for pedaco in pedacos)
    assert "".join(pedacos) == gigante
