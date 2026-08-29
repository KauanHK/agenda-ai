import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import Membership, UserActor
from app.core.roles import UserRole
from app.modules.scheduling_notifications.domain.entities import (
    SchedulingNotification,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


class FakeSchedulingNotificationsUnitOfWork:
    """Fake de `SchedulingNotificationsUnitOfWorkProtocol` para testar os use cases isoladamente."""

    def __init__(self, scheduling_notifications: AsyncMock) -> None:
        self.scheduling_notifications = scheduling_notifications
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


def make_notification(
    establishment_id: uuid.UUID, **overrides
) -> SchedulingNotification:
    now = datetime.now(UTC)
    defaults = dict(  # noqa: C408
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        scheduling_id=uuid.uuid7(),
        template_id=uuid.uuid7(),
        scheduled_at=now,
        status=NotificationStatus.pending,
        content_at_send=None,
        sent_at=None,
        attempts=0,
        last_attempt_at=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return SchedulingNotification(**defaults)


@pytest.fixture
def establishment_id() -> uuid.UUID:
    return uuid.uuid7()


@pytest.fixture
def notifications_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(notifications_repo: AsyncMock) -> FakeSchedulingNotificationsUnitOfWork:
    return FakeSchedulingNotificationsUnitOfWork(
        scheduling_notifications=notifications_repo
    )


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
