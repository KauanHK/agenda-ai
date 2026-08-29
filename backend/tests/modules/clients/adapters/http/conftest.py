import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import Membership, UserActor
from app.core.handlers import register_exception_handlers
from app.core.roles import UserRole
from app.modules.clients.adapters.db.factories import make_unit_of_work
from app.modules.clients.adapters.http.router import router as clients_router
from app.modules.clients.domain.entities import Client


class FakeClientsUnitOfWork:
    """Fake da UoW usada nos testes de HTTP, sobrepondo `make_unit_of_work`."""

    def __init__(self, clients: AsyncMock) -> None:
        self.clients = clients

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None


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
def client_entity(establishment_id) -> Client:
    now = datetime.now(UTC)
    return Client(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Cliente Teste",
        phone="11988887777",
        email="cliente@email.com",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def clients_repo(client_entity: Client) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = client_entity
    repo.create.return_value = client_entity
    repo.update.return_value = client_entity
    return repo


@pytest.fixture
def fake_uow(clients_repo: AsyncMock) -> FakeClientsUnitOfWork:
    return FakeClientsUnitOfWork(clients=clients_repo)


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
    fake_uow: FakeClientsUnitOfWork,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[make_unit_of_work] = lambda: fake_uow
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
