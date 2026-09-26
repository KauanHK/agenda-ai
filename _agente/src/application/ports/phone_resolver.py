"""Porta de resolução do telefone canônico de um contato."""

from typing import Protocol

from src.domain.entities import Channel


class PhoneResolverProtocol(Protocol):
    """Traduz a identidade do contato no canal para um telefone canônico.

    Síncrona e sem I/O na fase 1: o telefone é derivado de forma determinística
    do id do usuário no canal. A porta existe para que a troca por
    `request_contact` (ou por perguntar o número na conversa) seja uma
    substituição de adapter — inclusive uma assíncrona, quando for a hora de
    trocar a assinatura por `async def`.
    """

    def resolve(self, channel: Channel, channel_user_id: str) -> str:
        """Devolve o telefone canônico do contato, em E.164 sem o `+`."""
        ...
