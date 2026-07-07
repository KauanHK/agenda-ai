import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import Membership, UserActor
from app.core.handlers import register_exception_handlers
from app.modules.clients.api.deps import (
    get_clients_activator,
    get_clients_creator,
    get_clients_reader,
    get_clients_updater,
)
from app.modules.clients.api.router import router as clients_router
from app.modules.clients.application.activate import ClientsActivator
from app.modules.clients.application.create import ClientsCreator
from app.modules.clients.application.read import ClientsReader
from app.modules.clients.application.update import ClientsUpdater
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientRead
from app.modules.users.domain.enums import UserRole


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(
        clients_router, prefix="/establishments/{establishment_id}/clients"
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def client_model(establishment_id) -> Client:
    return Client(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Cliente Teste",
        phone="11988887777",
        email="cliente@email.com",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def client_read(client_model) -> ClientRead:
    return ClientRead.model_validate(client_model)


@pytest.fixture
def mock_clients_creator() -> AsyncMock:
    return AsyncMock(spec=ClientsCreator)


@pytest.fixture
def mock_clients_reader() -> AsyncMock:
    return AsyncMock(spec=ClientsReader)


@pytest.fixture
def mock_clients_updater() -> AsyncMock:
    return AsyncMock(spec=ClientsUpdater)


@pytest.fixture
def mock_clients_activator() -> AsyncMock:
    return AsyncMock(spec=ClientsActivator)


@pytest.fixture
def mock_actor(establishment_id) -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=False,
        memberships=(
            Membership(
                establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
            ),
        ),
    )


@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    mock_clients_creator: AsyncMock,
    mock_clients_reader: AsyncMock,
    mock_clients_updater: AsyncMock,
    mock_clients_activator: AsyncMock,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[get_clients_creator] = lambda: mock_clients_creator
    app.dependency_overrides[get_clients_reader] = lambda: mock_clients_reader
    app.dependency_overrides[get_clients_updater] = lambda: mock_clients_updater
    app.dependency_overrides[get_clients_activator] = lambda: mock_clients_activator
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
