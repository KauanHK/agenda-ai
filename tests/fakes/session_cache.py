"""Fakes de `SessionTokenCacheProtocol` para os testes de aplicação."""

from src.domain.entities import BookingSession


class FakeSessionCache:
    """Cache em memória, chaveado por telefone."""

    def __init__(self) -> None:
        self.store: dict[str, BookingSession] = {}
        self.put_calls: list[BookingSession] = []

    async def get(self, phone: str) -> BookingSession | None:
        return self.store.get(phone)

    async def put(self, session: BookingSession) -> None:
        self.put_calls.append(session)
        self.store[session.phone] = session


class UnavailableSessionCache:
    """Simula o Redis fora: `get` sempre em miss, `put` engolido."""

    def __init__(self) -> None:
        self.put_calls: list[BookingSession] = []

    async def get(self, phone: str) -> BookingSession | None:
        return None

    async def put(self, session: BookingSession) -> None:
        self.put_calls.append(session)
