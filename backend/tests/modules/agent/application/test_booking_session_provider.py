"""Testes de `BookingSessionProvider`: cache, margem de expiração e reemissão."""

import uuid
from datetime import UTC, datetime, timedelta

from app.modules.agent.application.use_cases.open_booking_session import (
    BookingSessionProvider,
)
from app.modules.agent.domain.entities import BookingSession, Channel, Contact
from tests.modules.agent.fakes.phone_resolver import FakePhoneResolver
from tests.modules.agent.fakes.session_cache import (
    FakeSessionCache,
    UnavailableSessionCache,
)
from tests.modules.agent.fakes.session_issuer import FakeSessionIssuer

_NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
_PHONE = "5547999123456"


def _contact() -> Contact:
    return Contact(
        channel=Channel.TELEGRAM,
        channel_user_id="42",
        display_name="Kauan",
        phone=_PHONE,
    )


def _session(*, token: str, expires_at: datetime) -> BookingSession:
    return BookingSession(
        token=token,
        phone=_PHONE,
        client_id=uuid.UUID("01a04f64-0000-7000-8000-000000000000"),
        client_name="Kauan",
        expires_at=expires_at,
        is_new_client=False,
    )


def _provider(
    *,
    issuer: FakeSessionIssuer,
    cache: FakeSessionCache | UnavailableSessionCache,
    resolver: FakePhoneResolver | None = None,
) -> BookingSessionProvider:
    return BookingSessionProvider(
        phone_resolver=resolver or FakePhoneResolver(_PHONE),
        issuer=issuer,
        cache=cache,
        clock=lambda: _NOW,
        refresh_margin_seconds=60,
    )


async def test_cache_hit_valido_nao_chama_o_issuer() -> None:
    cached = _session(token="cache", expires_at=_NOW + timedelta(minutes=5))
    cache = FakeSessionCache()
    cache.store[_PHONE] = cached
    issuer = FakeSessionIssuer(_session(token="novo", expires_at=_NOW + timedelta(minutes=10)))

    result = await _provider(issuer=issuer, cache=cache).for_contact(_contact())

    assert result is cached
    assert issuer.calls == []


async def test_sessao_expirando_dentro_da_margem_reemite() -> None:
    quase = _session(token="cache", expires_at=_NOW + timedelta(seconds=30))
    fresca = _session(token="novo", expires_at=_NOW + timedelta(minutes=10))
    cache = FakeSessionCache()
    cache.store[_PHONE] = quase
    issuer = FakeSessionIssuer(fresca)

    result = await _provider(issuer=issuer, cache=cache).for_contact(_contact())

    assert result is fresca
    assert issuer.calls == [(_PHONE, "Kauan")]
    assert cache.put_calls == [fresca]


async def test_cache_miss_reemite_e_guarda() -> None:
    fresca = _session(token="novo", expires_at=_NOW + timedelta(minutes=10))
    issuer = FakeSessionIssuer(fresca)
    cache = FakeSessionCache()

    result = await _provider(issuer=issuer, cache=cache).for_contact(_contact())

    assert result is fresca
    assert cache.store[_PHONE] is fresca


async def test_cache_indisponivel_reemite_e_segue() -> None:
    fresca = _session(token="novo", expires_at=_NOW + timedelta(minutes=10))
    issuer = FakeSessionIssuer(fresca)
    cache = UnavailableSessionCache()

    result = await _provider(issuer=issuer, cache=cache).for_contact(_contact())

    assert result is fresca
    assert issuer.calls == [(_PHONE, "Kauan")]
    assert cache.put_calls == [fresca]


async def test_usa_o_telefone_do_phone_resolver() -> None:
    resolver = FakePhoneResolver(_PHONE)
    fresca = _session(token="novo", expires_at=_NOW + timedelta(minutes=10))
    issuer = FakeSessionIssuer(fresca)

    await _provider(issuer=issuer, cache=FakeSessionCache(), resolver=resolver).for_contact(
        _contact()
    )

    assert resolver.calls == [(Channel.TELEGRAM, "42")]
