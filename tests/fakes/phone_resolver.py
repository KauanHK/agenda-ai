"""Fake de `PhoneResolverProtocol` para os testes de aplicação."""

from src.domain.entities import Channel


class FakePhoneResolver:
    """Devolve sempre o mesmo telefone e registra as chamadas."""

    def __init__(self, phone: str = "5547999123456") -> None:
        self.phone = phone
        self.calls: list[tuple[Channel, str]] = []

    def resolve(self, channel: Channel, channel_user_id: str) -> str:
        self.calls.append((channel, channel_user_id))
        return self.phone
