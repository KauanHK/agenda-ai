import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import UserActor
from app.core.handlers import register_exception_handlers
from app.modules.users.adapters.http.dependencies import (
    get_users_activator,
    get_users_reader,
    get_users_updater,
)
from app.modules.users.adapters.http.router import router as users_router
from app.modules.users.application.use_cases.activate import UsersActivator
from app.modules.users.application.use_cases.read import UsersReader
from app.modules.users.application.use_cases.update import UsersUpdater


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(users_router, prefix="/users")
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_users_reader() -> AsyncMock:
    return AsyncMock(spec=UsersReader)


@pytest.fixture
def mock_users_updater() -> AsyncMock:
    return AsyncMock(spec=UsersUpdater)


@pytest.fixture
def mock_users_activator() -> AsyncMock:
    return AsyncMock(spec=UsersActivator)


@pytest.fixture
def mock_current_actor() -> UserActor:
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=True,
        memberships=(),
    )


@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    mock_users_reader: AsyncMock,
    mock_users_updater: AsyncMock,
    mock_users_activator: AsyncMock,
    mock_current_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_current_actor

    app.dependency_overrides[get_users_reader] = lambda: mock_users_reader
    app.dependency_overrides[get_users_updater] = lambda: mock_users_updater
    app.dependency_overrides[get_users_activator] = lambda: mock_users_activator
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
