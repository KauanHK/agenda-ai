import uuid
from datetime import time
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_actor, get_current_establishment_actor
from app.core.actors.user import Membership, UserActor
from app.core.handlers import register_exception_handlers
from app.modules.operating_hours.api.deps import (
    get_operating_hours_reader,
    get_operating_hours_updater,
)
from app.modules.operating_hours.api.router import router as operating_hours_router
from app.modules.operating_hours.application.read import OperatingHoursReader
from app.modules.operating_hours.application.update import OperatingHoursUpdater
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.operating_hours.domain.schemas import OperatingHourRead
from app.modules.users.domain.enums import UserRole


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    application.include_router(
        operating_hours_router,
        prefix="/establishments/{establishment_id}/operating-hours",
        dependencies=[Depends(get_current_establishment_actor)],
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def hour_model(establishment_id) -> OperatingHour:
    return OperatingHour(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        weekday=0,
        start_time=time(9, 0),
        end_time=time(18, 0),
    )


@pytest.fixture
def hour_read(hour_model) -> OperatingHourRead:
    return OperatingHourRead.model_validate(hour_model)


@pytest.fixture
def mock_reader() -> AsyncMock:
    return AsyncMock(spec=OperatingHoursReader)


@pytest.fixture
def mock_updater() -> AsyncMock:
    return AsyncMock(spec=OperatingHoursUpdater)


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
    mock_reader: AsyncMock,
    mock_updater: AsyncMock,
    mock_actor: UserActor,
):
    async def _override_actor() -> UserActor:
        return mock_actor

    app.dependency_overrides[get_operating_hours_reader] = lambda: mock_reader
    app.dependency_overrides[get_operating_hours_updater] = lambda: mock_updater
    app.dependency_overrides[get_current_actor] = _override_actor

    yield

    app.dependency_overrides.clear()
