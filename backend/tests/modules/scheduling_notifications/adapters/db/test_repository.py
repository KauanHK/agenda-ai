import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling_notifications.adapters.db.models import (
    SchedulingNotification as SchedulingNotificationModel,
)
from app.modules.scheduling_notifications.adapters.db.repository import (
    SchedulingNotificationsRepository,
)
from app.modules.scheduling_notifications.domain.entities import (
    SchedulingNotification,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> SchedulingNotificationsRepository:
    return SchedulingNotificationsRepository(session=session)


@pytest.fixture
def model_row() -> SchedulingNotificationModel:
    now = datetime.now(UTC)
    return SchedulingNotificationModel(
        id=uuid.uuid7(),
        establishment_id=uuid.uuid7(),
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


def make_execute_result(rows: list) -> MagicMock:
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = rows
    return result_mock


async def test_get_pending_due_returns_due_notifications(repo, session, model_row):
    session.execute.return_value = make_execute_result([model_row])

    result = await repo.get_pending_due(limit=10)

    assert len(result) == 1
    assert isinstance(result[0], SchedulingNotification)
    assert result[0].id == model_row.id
    session.execute.assert_called_once()


async def test_get_pending_due_returns_empty_when_none_due(repo, session):
    session.execute.return_value = make_execute_result([])

    result = await repo.get_pending_due()

    assert result == []


async def test_get_pending_due_query_has_required_predicates(repo, session):
    session.execute.return_value = make_execute_result([])

    await repo.get_pending_due(limit=50)

    query = session.execute.call_args[0][0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "pending" in compiled
    assert "scheduled_at" in compiled
