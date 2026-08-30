"""Fakes de `OutboundMessengerProtocol` para os testes de aplicação."""

from src.domain.entities import Contact
from src.domain.exceptions import DeliveryError


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
        self.sent: list[tuple[Contact, str]] = []
        self.typing_signals: list[Contact] = []

    async def send_text(self, contact: Contact, text: str) -> None:
        if self._send_error is not None:
            raise self._send_error
        self.sent.append((contact, text))

    async def signal_typing(self, contact: Contact) -> None:
        self.typing_signals.append(contact)
        if self._typing_error is not None:
            raise self._typing_error
