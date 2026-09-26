"""Testes de `BookingSession.is_valid_at`, com foco na borda da expiração."""

import uuid
from datetime import UTC, datetime, timedelta

from app.modules.agent.domain.entities import BookingSession

_EXPIRES_AT = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)


def _session() -> BookingSession:
    return BookingSession(
        token="jwt",
        phone="5547999123456",
        client_id=uuid.UUID("01a04f64-0000-7000-8000-000000000000"),
        client_name="Kauan",
        expires_at=_EXPIRES_AT,
        is_new_client=True,
    )


def test_valida_antes_da_expiracao() -> None:
    assert _session().is_valid_at(_EXPIRES_AT - timedelta(seconds=1)) is True


def test_invalida_na_borda_exata_da_expiracao() -> None:
    assert _session().is_valid_at(_EXPIRES_AT) is False


def test_invalida_depois_da_expiracao() -> None:
    assert _session().is_valid_at(_EXPIRES_AT + timedelta(seconds=1)) is False
