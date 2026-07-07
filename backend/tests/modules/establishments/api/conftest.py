import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import UserActor
from app.modules.common.domain.enums import DocumentType
from app.modules.establishments.api.deps import (
    get_establishments_activator,
    get_establishments_creator,
    get_establishments_deleter,
    get_establishments_reader,
    get_establishments_updater,
)
from app.modules.establishments.api.router import router as establishments_router
from app.modules.establishments.application.activate import EstablishmentsActivator
from app.modules.establishments.application.create import EstablishmentsCreator
from app.modules.establishments.application.delete import EstablishmentsDeleter
from app.modules.establishments.application.read import EstablishmentsReader
from app.modules.establishments.application.update import EstablishmentsUpdater
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.domain.schemas import EstablishmentRead


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(establishments_router, prefix="/establishments")
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment() -> Establishment:
    return Establishment(
        id=uuid.uuid7(),
        name="Clínica Teste",
        document="11222333000181",
        document_type=DocumentType.CNPJ,
        timezone="America/Sao_Paulo",
        street="Rua das Flores",
        number="123",
        complement="",
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01310100",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_actor() -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=True,
        memberships=(),
    )


@pytest.fixture
def establishment_read(establishment) -> EstablishmentRead:
    return EstablishmentRead.model_validate(establishment)


@pytest.fixture
def mock_creator() -> AsyncMock:
    return AsyncMock(spec=EstablishmentsCreator)


@pytest.fixture
def mock_reader() -> AsyncMock:
    return AsyncMock(spec=EstablishmentsReader)


@pytest.fixture
def mock_updater() -> AsyncMock:
    return AsyncMock(spec=EstablishmentsUpdater)


@pytest.fixture
def mock_deleter() -> AsyncMock:
    return AsyncMock(spec=EstablishmentsDeleter)


@pytest.fixture
def mock_activator() -> AsyncMock:
    return AsyncMock(spec=EstablishmentsActivator)


@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    mock_creator: AsyncMock,
    mock_reader: AsyncMock,
    mock_updater: AsyncMock,
    mock_deleter: AsyncMock,
    mock_activator: AsyncMock,
    mock_actor: UserActor,
):
    app.dependency_overrides[get_establishments_creator] = lambda: mock_creator
    app.dependency_overrides[get_establishments_reader] = lambda: mock_reader
    app.dependency_overrides[get_establishments_updater] = lambda: mock_updater
    app.dependency_overrides[get_establishments_deleter] = lambda: mock_deleter
    app.dependency_overrides[get_establishments_activator] = lambda: mock_activator
    app.dependency_overrides[get_current_actor] = lambda: mock_actor

    yield

    app.dependency_overrides.clear()
