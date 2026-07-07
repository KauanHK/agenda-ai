import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import Membership, UserActor
from app.core.handlers import register_exception_handlers
from app.modules.services.api.deps import (
    get_services_activator,
    get_services_creator,
    get_services_reader,
    get_services_updater,
)
from app.modules.services.api.router import router as services_router
from app.modules.services.application.activate import ServicesActivator
from app.modules.services.application.create import ServicesCreator
from app.modules.services.application.read import ServicesReader
from app.modules.services.application.update import ServicesUpdater
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceRead
from app.modules.users.domain.enums import UserRole


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(
        services_router, prefix="/establishments/{establishment_id}/services"
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def service_model(establishment_id) -> Service:
    return Service(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Corte de Cabelo",
        description="Corte masculino tradicional",
        duration_minutes=30,
        price=Decimal("50.00"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def service_read(service_model) -> ServiceRead:
    return ServiceRead.model_validate(service_model)


@pytest.fixture
def mock_services_creator() -> AsyncMock:
    return AsyncMock(spec=ServicesCreator)


@pytest.fixture
def mock_services_reader() -> AsyncMock:
    return AsyncMock(spec=ServicesReader)


@pytest.fixture
def mock_services_updater() -> AsyncMock:
    return AsyncMock(spec=ServicesUpdater)


@pytest.fixture
def mock_services_activator() -> AsyncMock:
    return AsyncMock(spec=ServicesActivator)


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
    mock_services_creator: AsyncMock,
    mock_services_reader: AsyncMock,
    mock_services_updater: AsyncMock,
    mock_services_activator: AsyncMock,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[get_services_creator] = lambda: mock_services_creator
    app.dependency_overrides[get_services_reader] = lambda: mock_services_reader
    app.dependency_overrides[get_services_updater] = lambda: mock_services_updater
    app.dependency_overrides[get_services_activator] = lambda: mock_services_activator
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
