import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import UserActor
from app.core.handlers import register_exception_handlers
from app.modules.auth.adapters.http.dependencies import (
    get_auth_creator,
    get_auth_login,
    get_auth_refresh,
)
from app.modules.auth.adapters.http.router import router as auth_router
from app.modules.auth.application.use_cases.create import UsersCreator
from app.modules.auth.application.use_cases.login import AuthLogin
from app.modules.auth.application.use_cases.refresh import AuthRefresh


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(auth_router, prefix="/auth")
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_auth_login() -> AsyncMock:
    return AsyncMock(spec=AuthLogin)


@pytest.fixture
def mock_auth_refresh() -> AsyncMock:
    return AsyncMock(spec=AuthRefresh)


@pytest.fixture
def mock_auth_creator() -> AsyncMock:
    return AsyncMock(spec=UsersCreator)


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
    mock_auth_login: AsyncMock,
    mock_auth_refresh: AsyncMock,
    mock_auth_creator: AsyncMock,
    mock_current_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_current_actor

    app.dependency_overrides[get_auth_login] = lambda: mock_auth_login
    app.dependency_overrides[get_auth_refresh] = lambda: mock_auth_refresh
    app.dependency_overrides[get_auth_creator] = lambda: mock_auth_creator
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
