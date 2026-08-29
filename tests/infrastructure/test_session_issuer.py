"""Testes de `AgendaBotSessionIssuer` contra um dublê HTTP (respx)."""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from src.domain.exceptions import BookingSessionError, ClientBlockedError
from src.infrastructure.agendabot.http_client import build_agendabot_client
from src.infrastructure.agendabot.session_issuer import AgendaBotSessionIssuer

_BASE_URL = "https://agenda.test"
_ESTABLISHMENT_ID = uuid.UUID("01a04f5b-0e84-7530-be67-63f08e7b2269")
_SERVICE_KEY = "svc-secret-key"
_NOW = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
_URL = f"{_BASE_URL}/api/agent/{_ESTABLISHMENT_ID}/sessions"
_PHONE = "554792277579"

_CREATED_BODY = {
    "session_token": "jwt-real-do-estabelecimento",
    "expires_in_minutes": 10,
    "client": {"id": "01a04f64-0000-7000-8000-000000000000", "name": "Kauan"},
    "is_new_client": True,
}


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with build_agendabot_client(
        base_url=_BASE_URL, service_key=_SERVICE_KEY, timeout_seconds=5.0
    ) as c:
        yield c


def _issuer(client: httpx.AsyncClient, *, max_attempts: int = 3) -> AgendaBotSessionIssuer:
    return AgendaBotSessionIssuer(
        client,
        establishment_id=_ESTABLISHMENT_ID,
        clock=lambda: _NOW,
        max_attempts=max_attempts,
        backoff_base_seconds=0.0,
    )


async def test_201_devolve_a_sessao_com_expiracao_calculada(client: httpx.AsyncClient) -> None:
    with respx.mock:
        respx.post(_URL).mock(return_value=httpx.Response(201, json=_CREATED_BODY))
        session = await _issuer(client).issue(_PHONE, "Kauan")

    assert session.token == "jwt-real-do-estabelecimento"
    assert session.phone == _PHONE
    assert session.client_id == uuid.UUID("01a04f64-0000-7000-8000-000000000000")
    assert session.client_name == "Kauan"
    assert session.is_new_client is True
    assert session.expires_at == _NOW + timedelta(minutes=10)


async def test_manda_service_key_no_header_e_phone_name_no_corpo(
    client: httpx.AsyncClient,
) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(return_value=httpx.Response(201, json=_CREATED_BODY))
        await _issuer(client).issue(_PHONE, "Kauan")

    request = route.calls.last.request
    assert request.headers["X-Service-Key"] == _SERVICE_KEY
    assert json.loads(request.content) == {"phone": _PHONE, "name": "Kauan"}


async def test_sem_nome_o_corpo_leva_so_o_telefone(client: httpx.AsyncClient) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(return_value=httpx.Response(201, json=_CREATED_BODY))
        await _issuer(client).issue(_PHONE, None)

    assert json.loads(route.calls.last.request.content) == {"phone": _PHONE}


async def test_403_vira_client_blocked_sem_retry(client: httpx.AsyncClient) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(return_value=httpx.Response(403, json={"error_code": "x"}))
        with pytest.raises(ClientBlockedError):
            await _issuer(client).issue(_PHONE, "Kauan")

    assert route.call_count == 1


@pytest.mark.parametrize("status", [400, 401, 404, 409, 422])
async def test_4xx_vira_booking_session_error_sem_retry(
    client: httpx.AsyncClient, status: int
) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(return_value=httpx.Response(status))
        with pytest.raises(BookingSessionError):
            await _issuer(client).issue(_PHONE, "Kauan")

    assert route.call_count == 1


async def test_500_e_repetido_e_entao_vira_booking_session_error(
    client: httpx.AsyncClient,
) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(return_value=httpx.Response(500))
        with pytest.raises(BookingSessionError):
            await _issuer(client, max_attempts=3).issue(_PHONE, "Kauan")

    assert route.call_count == 3


async def test_erro_de_conexao_e_repetido_e_entao_vira_booking_session_error(
    client: httpx.AsyncClient,
) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(side_effect=httpx.ConnectError("recusado"))
        with pytest.raises(BookingSessionError):
            await _issuer(client, max_attempts=3).issue(_PHONE, "Kauan")

    assert route.call_count == 3


async def test_500_e_depois_201_devolve_a_sessao(client: httpx.AsyncClient) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(
            side_effect=[httpx.Response(500), httpx.Response(201, json=_CREATED_BODY)]
        )
        session = await _issuer(client, max_attempts=3).issue(_PHONE, "Kauan")

    assert session.token == "jwt-real-do-estabelecimento"
    assert route.call_count == 2


async def test_read_timeout_vira_booking_session_error_sem_retry(
    client: httpx.AsyncClient,
) -> None:
    with respx.mock:
        route = respx.post(_URL).mock(side_effect=httpx.ReadTimeout("lento"))
        with pytest.raises(BookingSessionError):
            await _issuer(client, max_attempts=3).issue(_PHONE, "Kauan")

    assert route.call_count == 1


async def test_corpo_201_malformado_vira_booking_session_error(
    client: httpx.AsyncClient,
) -> None:
    with respx.mock:
        respx.post(_URL).mock(return_value=httpx.Response(201, json={"sem": "campos"}))
        with pytest.raises(BookingSessionError):
            await _issuer(client).issue(_PHONE, "Kauan")


@pytest.mark.parametrize("status", [401, 403, 500])
async def test_service_key_nunca_aparece_em_mensagem_de_erro(
    client: httpx.AsyncClient, status: int
) -> None:
    with respx.mock:
        respx.post(_URL).mock(return_value=httpx.Response(status))
        with pytest.raises((BookingSessionError, ClientBlockedError)) as exc_info:
            await _issuer(client, max_attempts=1).issue(_PHONE, "Kauan")

    assert _SERVICE_KEY not in str(exc_info.value)
    assert _SERVICE_KEY not in repr(exc_info.value)
