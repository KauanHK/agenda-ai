import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastmcp import Client, FastMCP

from app.mcp.server import create_app
from app.modules.booking.adapters.mcp import tools as booking_tools
from app.modules.booking.domain.entities import (
    BookableService,
    CustomerScheduling,
    Slot,
)
from app.modules.booking.domain.exceptions import (
    NoProfessionalAvailableError,
    ServiceUnavailableError,
)
from app.modules.schedulings.domain.enums import SchedulingStatus

TOOL_NAMES = {
    "list_services",
    "list_available_slots",
    "create_scheduling",
    "list_my_schedulings",
    "cancel_scheduling",
    "reschedule_scheduling",
}

# Parâmetros que jamais podem aparecer no schema visto pelo modelo: identidade vem do
# token, e um LLM sob injeção de prompt não pode ter como sobrescrevê-la.
FORBIDDEN_PARAMS = {"actor", "uow", "client_id", "establishment_id", "phone"}


async def call(mcp: FastMCP, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Chama uma tool e devolve o envelope já desserializado."""

    async with Client(mcp) as client:
        result = await client.call_tool(tool, args)
    return json.loads(result.content[0].text)


def make_scheduling(**overrides: Any) -> CustomerScheduling:
    defaults: dict[str, Any] = {
        "id": uuid.uuid7(),
        "starts_at": datetime(2026, 9, 7, 9, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 9, 7, 10, 0, tzinfo=UTC),
        "status": SchedulingStatus.PENDING,
        "service_id": uuid.uuid7(),
        "service_name": "Corte de cabelo",
    }
    return CustomerScheduling(**(defaults | overrides))


class TestToolContract:
    async def test_registra_todas_as_tools(self, mcp_server: FastMCP) -> None:
        names = {tool.name for tool in await mcp_server.list_tools()}

        assert names == TOOL_NAMES

    async def test_nenhuma_tool_expoe_identidade_nos_parametros(
        self,
        mcp_server: FastMCP,
    ) -> None:
        for tool in await mcp_server.list_tools():
            params = set((tool.parameters or {}).get("properties", {}))
            assert not params & FORBIDDEN_PARAMS, f"{tool.name} expõe {params}"

    async def test_toda_tool_tem_descricao_para_o_modelo(
        self,
        mcp_server: FastMCP,
    ) -> None:
        for tool in await mcp_server.list_tools():
            assert tool.description, f"{tool.name} está sem docstring"

    @pytest.mark.parametrize(
        ("tool", "params"),
        [
            ("list_available_slots", {"service_id", "day"}),
            ("create_scheduling", {"service_id", "starts_at"}),
            ("cancel_scheduling", {"scheduling_id"}),
            ("reschedule_scheduling", {"scheduling_id", "new_starts_at"}),
        ],
    )
    async def test_parametros_esperados(
        self,
        mcp_server: FastMCP,
        tool: str,
        params: set[str],
    ) -> None:
        found = next(t for t in await mcp_server.list_tools() if t.name == tool)

        assert set((found.parameters or {}).get("properties", {})) == params


class TestEnvelope:
    async def test_sucesso_devolve_envelope_com_data(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service_id = uuid.uuid7()
        reader = AsyncMock()
        reader.list_services.return_value = [
            BookableService(
                id=service_id,
                name="Corte de cabelo",
                description="Corte masculino",
                duration_minutes=60,
                price=Decimal("50.00"),
            )
        ]
        monkeypatch.setattr(booking_tools, "BookingReader", lambda uow: reader)

        envelope = await call(mcp_server, "list_services", {})

        assert envelope["success"] is True
        assert envelope["data"] == [
            {
                "service_id": str(service_id),
                "name": "Corte de cabelo",
                "description": "Corte masculino",
                "duration_minutes": 60,
                "price": "50.00",
            }
        ]

    async def test_erro_de_dominio_vira_error_code(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reader = AsyncMock()
        reader.list_slots.side_effect = ServiceUnavailableError()
        monkeypatch.setattr(booking_tools, "BookingReader", lambda uow: reader)

        envelope = await call(
            mcp_server,
            "list_available_slots",
            {"service_id": str(uuid.uuid7()), "day": "2026-09-07"},
        )

        assert envelope["success"] is False
        assert envelope["error_code"] == "service_unavailable"
        assert envelope["message"]

    async def test_erro_inesperado_nao_vaza_detalhes(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reader = AsyncMock()
        reader.list_services.side_effect = RuntimeError("connection string secreta")
        monkeypatch.setattr(booking_tools, "BookingReader", lambda uow: reader)

        envelope = await call(mcp_server, "list_services", {})

        assert envelope["success"] is False
        assert envelope["error_code"] == "internal_error"
        assert "secreta" not in json.dumps(envelope)

    async def test_horario_indisponivel_tem_codigo_proprio(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        creator = AsyncMock()
        creator.create.side_effect = NoProfessionalAvailableError()
        monkeypatch.setattr(booking_tools, "BookingCreator", lambda uow: creator)

        envelope = await call(
            mcp_server,
            "create_scheduling",
            {
                "service_id": str(uuid.uuid7()),
                "starts_at": "2026-09-07T09:00:00-03:00",
            },
        )

        assert envelope["error_code"] == "no_professional_available"


class TestToolBehaviour:
    async def test_slots_nao_revelam_o_profissional(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        reader = AsyncMock()
        reader.list_slots.return_value = [
            Slot(
                starts_at=datetime(2026, 9, 7, 9, 0, tzinfo=UTC),
                ends_at=datetime(2026, 9, 7, 10, 0, tzinfo=UTC),
                user_id=uuid.uuid7(),
            )
        ]
        monkeypatch.setattr(booking_tools, "BookingReader", lambda uow: reader)

        envelope = await call(
            mcp_server,
            "list_available_slots",
            {"service_id": str(uuid.uuid7()), "day": "2026-09-07"},
        )

        assert envelope["data"] == [
            {
                "starts_at": "2026-09-07T09:00:00+00:00",
                "ends_at": "2026-09-07T10:00:00+00:00",
            }
        ]

    async def test_create_repassa_o_ator_da_sessao(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
        actor,
    ) -> None:
        creator = AsyncMock()
        creator.create.return_value = make_scheduling()
        monkeypatch.setattr(booking_tools, "BookingCreator", lambda uow: creator)

        service_id = uuid.uuid7()
        await call(
            mcp_server,
            "create_scheduling",
            {
                "service_id": str(service_id),
                "starts_at": "2026-09-07T09:00:00-03:00",
            },
        )

        kwargs = creator.create.await_args.kwargs
        assert kwargs["actor"] == actor
        assert kwargs["service_id"] == service_id

    async def test_cancel_devolve_o_agendamento_cancelado(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scheduling_id = uuid.uuid7()
        canceller = AsyncMock()
        canceller.cancel.return_value = make_scheduling(
            id=scheduling_id, status=SchedulingStatus.CANCELLED
        )
        monkeypatch.setattr(booking_tools, "BookingCanceller", lambda uow: canceller)

        envelope = await call(
            mcp_server, "cancel_scheduling", {"scheduling_id": str(scheduling_id)}
        )

        assert envelope["data"]["scheduling_id"] == str(scheduling_id)
        assert envelope["data"]["status"] == "cancelled"

    async def test_reschedule_repassa_o_novo_horario(
        self,
        mcp_server: FastMCP,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rescheduler = AsyncMock()
        rescheduler.reschedule.return_value = make_scheduling()
        monkeypatch.setattr(
            booking_tools, "BookingRescheduler", lambda uow: rescheduler
        )

        scheduling_id = uuid.uuid7()
        await call(
            mcp_server,
            "reschedule_scheduling",
            {
                "scheduling_id": str(scheduling_id),
                "new_starts_at": "2026-09-08T14:00:00-03:00",
            },
        )

        kwargs = rescheduler.reschedule.await_args.kwargs
        assert kwargs["scheduling_id"] == scheduling_id
        assert kwargs["new_starts_at"].isoformat() == "2026-09-08T14:00:00-03:00"


class TestServerAuthentication:
    async def test_recusa_conexao_sem_token(self) -> None:
        """
        O servidor real (com `SessionTokenVerifier`) responde 401 antes de qualquer
        tool rodar.
        """

        app = create_app().http_app(path="/mcp", stateless_http=True)

        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )

        assert response.status_code == 401

    async def test_recusa_token_invalido(self) -> None:
        app = create_app().http_app(path="/mcp", stateless_http=True)

        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer token-falso",
                },
            )

        assert response.status_code == 401
