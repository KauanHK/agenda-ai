"""Caso de uso: obter uma sessão válida para o contato, reaproveitando o cache."""

from collections.abc import Callable
from datetime import datetime, timedelta

from app.modules.agent.application.ports.booking_session import (
    BookingSessionIssuerProtocol,
)
from app.modules.agent.application.ports.phone_resolver import PhoneResolverProtocol
from app.modules.agent.application.ports.session_cache import SessionTokenCacheProtocol
from app.modules.agent.domain.entities import BookingSession, Contact


class BookingSessionProvider:
    """Devolve uma sessão válida para o contato, reaproveitando o cache.

    A política "usa o cache; senão emite; e guarda" é decisão de aplicação — por
    isso isto é um caso de uso, e não um adapter.
    """

    def __init__(
        self,
        phone_resolver: PhoneResolverProtocol,
        issuer: BookingSessionIssuerProtocol,
        cache: SessionTokenCacheProtocol,
        clock: Callable[[], datetime],
        refresh_margin_seconds: int,
    ) -> None:
        self._phone_resolver = phone_resolver
        self._issuer = issuer
        self._cache = cache
        self._clock = clock
        self._refresh_margin_seconds = refresh_margin_seconds

    async def for_contact(self, contact: Contact) -> BookingSession:
        """Resolve o telefone, tenta o cache e emite uma sessão nova se preciso."""
        phone = self._phone_resolver.resolve(contact.channel, contact.channel_user_id)
        usable_until = self._clock() + timedelta(seconds=self._refresh_margin_seconds)

        cached = await self._cache.get(phone)
        if cached is not None and cached.is_valid_at(usable_until):
            return cached

        session = await self._issuer.issue(phone, contact.display_name)
        await self._cache.put(session)
        return session
