"""Erros da conversa com a Bot API do Telegram.

A mensagem nunca carrega o token do bot nem o segredo do webhook: estes erros podem
ser logados com o stacktrace inteiro.
"""


class InvalidBotTokenError(Exception):
    """A Bot API respondeu `401` ou `404`: token revogado, inexistente ou malformado."""


class TelegramApiError(Exception):
    """Falha de transporte, timeout, `429`, `5xx` ou `ok: false` por outro motivo.

    Não é base de `InvalidBotTokenError` de propósito: quem chama trata os dois de
    forma diferente (token revogado é definitivo; o resto vale tentar de novo).
    """
