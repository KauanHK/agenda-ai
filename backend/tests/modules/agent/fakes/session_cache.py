"""Fakes de `SessionTokenCacheProtocol` para os testes de aplicação."""

import uuid

from app.modules.agent.domain.entities import BookingSession


class FakeSessionCache:
    """Cache em memória, chaveado por (estabelecimento, telefone)."""

    def __init__(self) -> None:
        self.store: dict[tuple[uuid.UUID, str], BookingSession] = {}
        self.get_calls: list[tuple[uuid.UUID, str]] = []
        self.put_calls: list[BookingSession] = []

    async def get(self, establishment_id: uuid.UUID, phone: str) -> BookingSession | None:
        self.get_calls.append((establishment_id, phone))
        return self.store.get((establishment_id, phone))

    async def put(self, session: BookingSession) -> None:
        self.put_calls.append(session)
        self.store[session.establishment_id, session.phone] = session


class UnavailableSessionCache:
    """Simula o Redis fora: `get` sempre em miss, `put` engolido."""

    def __init__(self) -> None:
        self.put_calls: list[BookingSession] = []

    async def get(self, establishment_id: uuid.UUID, phone: str) -> BookingSession | None:
        return None

    async def put(self, session: BookingSession) -> None:
        self.put_calls.append(session)
