import uuid
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
from app.modules.operating_hours.adapters.db.factories import make_unit_of_work
from app.modules.operating_hours.adapters.http.router import (
    router as operating_hours_router,
)


class FakeOperatingHoursUnitOfWork:
    """Fake da UoW usada nos testes de HTTP, sobrepondo `make_unit_of_work`."""

    def __init__(self, operating_hours: AsyncMock) -> None:
        self.operating_hours = operating_hours

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
        operating_hours_router,
        prefix="/establishments/{establishment_id}/operating-hours",
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def operating_hours_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def fake_uow(operating_hours_repo: AsyncMock) -> FakeOperatingHoursUnitOfWork:
    return FakeOperatingHoursUnitOfWork(operating_hours=operating_hours_repo)


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
    fake_uow: FakeOperatingHoursUnitOfWork,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[make_unit_of_work] = lambda: fake_uow
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
