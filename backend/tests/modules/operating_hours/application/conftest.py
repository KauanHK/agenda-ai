import uuid
from datetime import time
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.users.domain.enums import UserRole


def make_operating_hour(
    establishment_id: uuid.UUID,
    weekday: int = 0,
    start_time: time = time(9, 0),
    end_time: time = time(18, 0),
) -> OperatingHour:
    return OperatingHour(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
    )


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(),
        is_global_admin=is_global_admin,
        memberships=memberships,
    )


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def hour_model(establishment_id) -> OperatingHour:
    return make_operating_hour(establishment_id=establishment_id)


@pytest.fixture
def mock_repo(hour_model) -> AsyncMock:
    repo = AsyncMock(spec=OperatingHoursRepository)
    repo.list_by_establishment.return_value = [hour_model]
    repo.replace_all.return_value = [hour_model]
    return repo


@pytest.fixture
def mock_uow(mock_repo) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    uow.repository.return_value = mock_repo
    return uow


@pytest.fixture
def admin_user(establishment_id) -> UserActor:
    return make_actor(
        establishment_id=establishment_id, role=UserRole.ESTABLISHMENT_ADMIN
    )


@pytest.fixture
def member_user(establishment_id) -> UserActor:
    return make_actor(establishment_id=establishment_id, role=UserRole.MEMBER)


@pytest.fixture
def global_admin_user() -> UserActor:
    return make_actor(is_global_admin=True)
