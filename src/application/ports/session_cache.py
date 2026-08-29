"""Porta de cache do token de sessão."""

from typing import Protocol

from src.domain.entities import BookingSession


class SessionTokenCacheProtocol(Protocol):
    """Guarda a sessão emitida enquanto ela vale, para evitar reemissão.

    Cache indisponível degrada performance, não funcionalidade: um `get` que
    falha devolve `None` e um `put` que falha não levanta — o
    `BookingSessionProvider` apenas emite um token novo.
    """

    async def get(self, phone: str) -> BookingSession | None:
        """Devolve a sessão cacheada e ainda válida para o telefone, ou `None`."""
        ...

    async def put(self, session: BookingSession) -> None:
        """Guarda a sessão até pouco antes de ela expirar."""
        ...
