"""Fakes de `OutboundMessengerProtocol` para os testes de aplicação."""

from app.modules.agent.domain.entities import ConversationRef
from app.modules.agent.domain.exceptions import DeliveryError


class FakeMessenger:
    """Registra o que foi enviado e sinalizado; pode levantar sob demanda."""

    def __init__(
        self,
        *,
        send_error: DeliveryError | None = None,
        typing_error: Exception | None = None,
    ) -> None:
        self._send_error = send_error
        self._typing_error = typing_error
        self.sent: list[tuple[ConversationRef, str]] = []
        self.typing_signals: list[ConversationRef] = []

    async def send_text(self, conversation: ConversationRef, text: str) -> None:
        if self._send_error is not None:
            raise self._send_error
        self.sent.append((conversation, text))

    async def signal_typing(self, conversation: ConversationRef) -> None:
        self.typing_signals.append(conversation)
        if self._typing_error is not None:
            raise self._typing_error
