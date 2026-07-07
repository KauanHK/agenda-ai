import uuid
from unittest.mock import AsyncMock, MagicMock

from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import SchedulingNotificationsRepository


async def test_get_pending_due_returns_due_notifications():
    notification = MagicMock(spec=SchedulingNotification)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = [notification]
    mock_session.execute.return_value = mock_result

    repo = SchedulingNotificationsRepository(mock_session)
    result = await repo.get_pending_due(limit=10)

    assert result == [notification]
    mock_session.execute.assert_called_once()


async def test_get_pending_due_returns_empty_when_none_due():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = SchedulingNotificationsRepository(mock_session)
    result = await repo.get_pending_due()

    assert result == []


async def test_get_pending_due_query_has_required_predicates():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value = []
    mock_session.execute.return_value = mock_result

    repo = SchedulingNotificationsRepository(mock_session)
    await repo.get_pending_due(limit=50)

    query = mock_session.execute.call_args[0][0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "pending" in compiled
    assert "scheduled_at" in compiled
