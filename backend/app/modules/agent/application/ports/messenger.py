"""Porta de entrega da resposta do agente de volta ao canal de origem."""

from typing import Protocol

from app.modules.agent.domain.entities import ConversationRef


class OutboundMessengerProtocol(Protocol):
    """Entrega texto na conversa e sinaliza o preparo da resposta.

    São dois motivos de mudança diferentes — como se entrega uma resposta e
    como se mostra "digitando" —, mas a mesma API do canal cobre os dois, então
    ficam na mesma porta. Trocar o Telegram por outro canal troca só o adapter.
    """

    async def send_text(self, conversation: ConversationRef, text: str) -> None:
        """Entrega um texto na conversa.

        A conversa, e não o contato, diz por qual bot responder: canal,
        estabelecimento e usuário.

        Raises:
            DeliveryError: Se a resposta não puder ser entregue ao canal.
        """
        ...

    async def signal_typing(self, conversation: ConversationRef) -> None:
        """Sinaliza ao canal que a resposta está sendo produzida.

        Falha em silêncio: um indicador de digitação que não apareceu não é
        motivo para abortar o turno.
        """
        ...
