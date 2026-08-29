import uuid
from datetime import time
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.core.roles import UserRole
from app.modules.operating_hours.domain.entities import OperatingHour


class FakeOperatingHoursUnitOfWork:
    """Fake de `OperatingHoursUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, operating_hours: AsyncMock) -> None:
        self.operating_hours = operating_hours
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        return None


def make_actor(
    is_global_admin: bool = False,
    establishment_id: uuid.UUID | None = None,
    role: str | None = None,
) -> UserActor:
    memberships: tuple[Membership, ...] = ()
    if establishment_id is not None and role is not None:
        memberships = (Membership(establishment_id=establishment_id, role=role),)
    return UserActor(
        user_id=uuid.uuid7(), is_global_admin=is_global_admin, memberships=memberships
    )


def make_operating_hour(establishment_id: uuid.UUID, **overrides) -> OperatingHour:
    defaults = dict(  # noqa: C408
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        weekday=1,
        start_time=time(8, 0),
        end_time=time(18, 0),
    )
    defaults.update(overrides)
    return OperatingHour(**defaults)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def operating_hours_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(operating_hours_repo: AsyncMock) -> FakeOperatingHoursUnitOfWork:
    return FakeOperatingHoursUnitOfWork(operating_hours=operating_hours_repo)


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
