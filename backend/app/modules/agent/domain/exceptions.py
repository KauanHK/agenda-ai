"""Erros esperados do agente.

Cada erro carrega o `user_message` — a frase que o canal mostra ao cliente quando
algo dá errado. Isso mantém a decisão "o que o cliente lê" no domínio, e não
espalhada por `try/except` nos adapters.
"""


class AgentError(Exception):
    """Base de todo erro esperado do agente."""

    user_message: str = "Tive um problema aqui. Pode tentar de novo em instantes?"


class BookingSessionError(AgentError):
    """Não foi possível abrir a sessão do cliente no AgendaBot."""


class ClientBlockedError(BookingSessionError):
    """O cliente existe mas está inativo no estabelecimento."""

    user_message = "Não consigo te atender por aqui. Fale direto com o estabelecimento."


class AgentUnavailableError(AgentError):
    """O LLM falhou ou estourou o tempo."""


class ConversationStateError(AgentError):
    """Não foi possível ler ou gravar o estado da conversa."""


class DeliveryError(AgentError):
    """A resposta não pôde ser entregue ao canal."""


class WebhookRegistrationError(AgentError):
    """O canal recusou registrar ou informar o webhook."""


class InvalidPhoneError(AgentError):
    """O telefone do contato não pôde ser determinado."""
