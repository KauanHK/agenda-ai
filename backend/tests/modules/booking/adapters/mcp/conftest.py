import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from app.core.actors.customer import CustomerActor
from app.modules.booking.adapters.mcp import tools as booking_tools


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def client_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def actor(establishment_id: uuid.UUID, client_id: uuid.UUID) -> CustomerActor:
    return CustomerActor(
        establishment_id=establishment_id,
        client_id=client_id,
        phone="+5547999998888",
    )


@pytest.fixture
def fake_uow() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def build_server(
    monkeypatch: pytest.MonkeyPatch,
    actor: CustomerActor,
    fake_uow: AsyncMock,
) -> Callable[[], FastMCP]:
    """
    Monta um servidor MCP com as dependências trocadas por fakes.

    Os `Depends(...)` são avaliados quando `register_tools` define as funções, então o
    monkeypatch precisa acontecer antes — por isso a construção do servidor é adiada
    para dentro da fixture.
    """

    async def fake_actor() -> CustomerActor:
        return actor

    @asynccontextmanager
    async def fake_get_uow() -> AsyncIterator[Any]:
        yield fake_uow

    monkeypatch.setattr(booking_tools, "get_customer_actor", fake_actor)
    monkeypatch.setattr(booking_tools, "get_booking_uow", fake_get_uow)

    def _build() -> FastMCP:
        mcp = FastMCP("test")
        booking_tools.register_tools(mcp)
        return mcp

    return _build


@pytest.fixture
def mcp_server(build_server: Callable[[], FastMCP]) -> FastMCP:
    return build_server()
