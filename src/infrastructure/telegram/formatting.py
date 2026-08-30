"""Funções puras que preparam o texto do LLM para a Bot API do Telegram.

Decisão do doc 07: **enviar sem `parse_mode`**. MarkdownV2 exige escapar 18
caracteres e um escape errado devolve `400` — o cliente não recebe nada.
`to_telegram_text` só remove as marcações que ficariam feias em texto puro;
`split_for_telegram` respeita o teto de 4096 caracteres da API sem cortar
palavra no meio.
"""

import re

TELEGRAM_MAX_CHARS = 4096

_BOLD_MARKER = re.compile(r"\*\*")
_HEADING_PREFIX = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]*")
_BLANK_LINES = re.compile(r"\n{3,}")
_WHITESPACE_RUN = re.compile(r"(\s+)")


def to_telegram_text(raw: str) -> str:
    """Normaliza o texto do LLM para envio seguro em texto puro.

    Remove os `**` de negrito e os `#` de título que o modelo às vezes emite, e
    colapsa sequências de linhas em branco. Não escapa nada: o envio é sem
    `parse_mode`.
    """
    without_bold = _BOLD_MARKER.sub("", raw)
    without_headings = _HEADING_PREFIX.sub("", without_bold)
    collapsed = _BLANK_LINES.sub("\n\n", without_headings)
    return collapsed.strip()


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_CHARS) -> list[str]:
    """Quebra o texto em pedaços de no máximo `limit` caracteres.

    Quebra primeiro entre parágrafos; um parágrafo maior que o limite é
    quebrado entre palavras, e só uma palavra sozinha maior que o limite é
    cortada no meio. Um texto vazio devolve uma lista vazia — a API rejeita
    mensagem sem conteúdo.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= limit:
            current = paragraph
        else:
            chunks.extend(_split_paragraph(paragraph, limit))
    if current:
        chunks.append(current)
    return chunks


def _split_paragraph(paragraph: str, limit: int) -> list[str]:
    """Quebra um parágrafo longo entre palavras, cortando só a palavra gigante."""
    pieces: list[str] = []
    current = ""
    for token in _WHITESPACE_RUN.split(paragraph):
        if not token:
            continue
        if len(current) + len(token) <= limit:
            current += token
            continue
        if current.strip():
            pieces.append(current.strip())
            current = ""
        if len(token) <= limit:
            current = token
            continue
        for offset in range(0, len(token), limit):
            pieces.append(token[offset : offset + limit])
    if current.strip():
        pieces.append(current.strip())
    return pieces
