"""Porta de entrega da resposta do agente de volta ao canal de origem."""

from typing import Protocol

from src.domain.entities import Contact


class OutboundMessengerProtocol(Protocol):
    """Entrega texto ao contato no canal e sinaliza o preparo da resposta.

    São dois motivos de mudança diferentes — como se entrega uma resposta e
    como se mostra "digitando" —, mas a mesma API do canal cobre os dois, então
    ficam na mesma porta. Trocar o Telegram por outro canal troca só o adapter.
    """

    async def send_text(self, contact: Contact, text: str) -> None:
        """Entrega um texto ao contato.

        Raises:
            DeliveryError: Se a resposta não puder ser entregue ao canal.
        """
        ...

    async def signal_typing(self, contact: Contact) -> None:
        """Sinaliza ao canal que a resposta está sendo produzida.

        Falha em silêncio: um indicador de digitação que não apareceu não é
        motivo para abortar o turno.
        """
        ...
