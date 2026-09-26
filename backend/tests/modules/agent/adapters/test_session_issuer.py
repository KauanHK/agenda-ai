"""Testes de `InProcessSessionIssuer` com um UoW falso do booking."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.security.mcp_tokens import decode_client_mcp_session_token
from app.core.settings import settings
from app.modules.agent.adapters.booking.session_issuer import InProcessSessionIssuer
from app.modules.agent.domain.exceptions import (
    BookingSessionError,
    ClientBlockedError,
    InvalidPhoneError,
)
from tests.modules.booking.application.use_cases.conftest import FakeBookingUnitOfWork
from tests.modules.booking.application.use_cases.test_sessions import make_client

_ESTABLISHMENT_ID = uuid.uuid7()
_NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
_PHONE = "5547999998888"


def _establishments(*, active: bool = True, exists: bool = True) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id_or_none.return_value = (
        MagicMock(is_active=active) if exists else None
    )
    return repo


def _issuer(clients: AsyncMock, establishments: AsyncMock | None = None) -> InProcessSessionIssuer:
    establishments = establishments or _establishments()
    return InProcessSessionIssuer(
        establishment_id=_ESTABLISHMENT_ID,
        clock=lambda: _NOW,
        uow_factory=lambda: FakeBookingUnitOfWork(
            clients=clients, establishments=establishments
        ),
    )


def _clients(**overrides: object) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_establishment_and_phone.return_value = make_client(
        _ESTABLISHMENT_ID, **overrides
    )
    return repo


async def test_emite_a_sessao_do_cliente_existente() -> None:
    clients = _clients(name="Maria")
    client = clients.get_by_establishment_and_phone.return_value

    session = await _issuer(clients).issue(_PHONE, "Maria")

    assert session.phone == _PHONE
    assert session.client_id == client.id
    assert session.client_name == "Maria"
    assert session.is_new_client is False
    assert session.expires_at == _NOW + timedelta(
        minutes=settings.MCP_SESSION_TOKEN_EXPIRES_MINUTES
    )
    assert decode_client_mcp_session_token(session.token)["client_id"] == client.id


async def test_cliente_novo_e_repassado() -> None:
    clients = _clients()
    clients.create.return_value = clients.get_by_establishment_and_phone.return_value
    clients.get_by_establishment_and_phone.return_value = None

    session = await _issuer(clients).issue(_PHONE, "João")

    assert session.is_new_client is True


async def test_cliente_inativo_vira_client_blocked() -> None:
    with pytest.raises(ClientBlockedError):
        await _issuer(_clients(is_active=False)).issue(_PHONE, None)


async def test_telefone_invalido_vira_invalid_phone() -> None:
    with pytest.raises(InvalidPhoneError):
        await _issuer(_clients()).issue("12", None)


@pytest.mark.parametrize(
    "establishments",
    [_establishments(exists=False), _establishments(active=False)],
    ids=["inexistente", "inativo"],
)
async def test_estabelecimento_indisponivel_vira_booking_session_error(
    establishments: AsyncMock,
) -> None:
    with pytest.raises(BookingSessionError) as exc_info:
        await _issuer(_clients(), establishments).issue(_PHONE, None)

    assert type(exc_info.value) is BookingSessionError


@pytest.mark.parametrize(
    "error",
    [OperationalError("SELECT 1", {}, Exception("down")), ConnectionRefusedError()],
    ids=["sqlalchemy", "os"],
)
async def test_falha_de_infra_vira_booking_session_error(error: Exception) -> None:
    clients = _clients()
    clients.get_by_establishment_and_phone.side_effect = error

    with pytest.raises(BookingSessionError) as exc_info:
        await _issuer(clients).issue(_PHONE, None)

    assert type(exc_info.value) is BookingSessionError


async def test_conflito_tenta_de_novo_uma_vez_e_emite() -> None:
    clients = _clients()
    existing = clients.get_by_establishment_and_phone.return_value
    # 1ª tentativa: não acha e perde a corrida no INSERT; 2ª: acha o cliente criado.
    clients.get_by_establishment_and_phone.side_effect = [None, existing]
    clients.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    session = await _issuer(clients).issue(_PHONE, None)

    assert session.client_id == existing.id
    assert session.is_new_client is False
    assert clients.get_by_establishment_and_phone.await_count == 2


async def test_conflito_repetido_vira_booking_session_error() -> None:
    clients = _clients()
    clients.get_by_establishment_and_phone.return_value = None
    clients.create.side_effect = IntegrityError("INSERT", {}, Exception("dup"))

    with pytest.raises(BookingSessionError) as exc_info:
        await _issuer(clients).issue(_PHONE, None)

    assert type(exc_info.value) is BookingSessionError
    assert clients.create.await_count == 2
