import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor
from app.core.actors.user import UserActor
from app.core.handlers import register_exception_handlers
from app.modules.memberships.adapters.http.dependencies import (
    get_membership_activator,
    get_membership_creator,
    get_membership_deleter,
    get_membership_reader,
    get_membership_updater,
)
from app.modules.memberships.adapters.http.router import router, user_router
from app.modules.memberships.application.use_cases.activate import (
    MembershipActivator,
)
from app.modules.memberships.application.use_cases.create import MembershipCreator
from app.modules.memberships.application.use_cases.delete import MembershipDeleter
from app.modules.memberships.application.use_cases.read import MembershipsReader
from app.modules.memberships.application.use_cases.update import MembershipUpdater


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(
        router, prefix="/establishments/{establishment_id}/members"
    )
    application.include_router(user_router, prefix="/users")
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_reader() -> AsyncMock:
    return AsyncMock(spec=MembershipsReader)


@pytest.fixture
def mock_creator() -> AsyncMock:
    return AsyncMock(spec=MembershipCreator)


@pytest.fixture
def mock_updater() -> AsyncMock:
    return AsyncMock(spec=MembershipUpdater)


@pytest.fixture
def mock_deleter() -> AsyncMock:
    return AsyncMock(spec=MembershipDeleter)


@pytest.fixture
def mock_activator() -> AsyncMock:
    return AsyncMock(spec=MembershipActivator)


@pytest.fixture
def mock_current_actor() -> UserActor:
    return UserActor(user_id=uuid.uuid7(), is_global_admin=True, memberships=())


@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    mock_reader: AsyncMock,
    mock_creator: AsyncMock,
    mock_updater: AsyncMock,
    mock_deleter: AsyncMock,
    mock_activator: AsyncMock,
    mock_current_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_current_actor

    app.dependency_overrides[get_membership_reader] = lambda: mock_reader
    app.dependency_overrides[get_membership_creator] = lambda: mock_creator
    app.dependency_overrides[get_membership_updater] = lambda: mock_updater
    app.dependency_overrides[get_membership_deleter] = lambda: mock_deleter
    app.dependency_overrides[get_membership_activator] = lambda: mock_activator
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
