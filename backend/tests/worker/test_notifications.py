import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.evolution import EvolutionAPIError
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.scheduling_notifications.infra.repository import (
    SchedulingNotificationsRepository,
)
from app.worker.notifications import _dispatch_pending, _send_notification


def _make_notification(
    status: NotificationStatus = NotificationStatus.pending,
) -> MagicMock:
    n = MagicMock(spec=SchedulingNotification)
    n.id = uuid.uuid7()
    n.status = status
    n.scheduling_id = uuid.uuid7()
    n.template_id = uuid.uuid7()
    n.attempts = 0
    n.content_at_send = None
    n.last_error = None
    n.sent_at = None
    n.last_attempt_at = None
    return n


def _make_scheduling() -> MagicMock:
    s = MagicMock()
    s.client_id = uuid.uuid7()
    s.service_id = uuid.uuid7()
    s.starts_at = datetime(2026, 6, 1, 14, 0, tzinfo=UTC)
    return s


def _make_client(name: str = "João Silva", phone: str = "5548999999999") -> MagicMock:
    c = MagicMock()
    c.name = name
    c.phone = phone
    return c


def _make_service(name: str = "Corte de Cabelo") -> MagicMock:
    s = MagicMock()
    s.name = name
    return s


def _make_template(
    content: str = "Olá {cliente}, seu {servico} é em {data} às {hora}",
) -> MagicMock:
    t = MagicMock()
    t.content = content
    return t


def _mock_session_with_notification(notification: MagicMock) -> AsyncMock:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = notification
    mock_session.execute.return_value = mock_result
    return mock_session


async def test_send_notification_success():
    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.sent
    assert notification.sent_at is not None
    assert notification.last_attempt_at is not None
    assert notification.attempts == 1
    assert notification.content_at_send is not None
    mock_send.assert_called_once_with(
        "5548999999999",
        notification.content_at_send,
    )


async def test_send_notification_marks_failed_on_evolution_api_error():
    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch(
        "app.worker.notifications.send_text",
        side_effect=EvolutionAPIError(500, "timeout"),
    ):
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert "timeout" in notification.last_error
    assert notification.attempts == 1
    assert notification.last_attempt_at is not None


async def test_send_notification_skips_when_no_row_found():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(uuid.uuid7(), mock_session)

    mock_send.assert_not_called()
    mock_session.get.assert_not_called()


async def test_send_notification_marks_failed_on_unknown_template_variable():
    notification = _make_notification()
    scheduling = _make_scheduling()
    client = _make_client()
    service = _make_service()
    template = _make_template(content="Olá {cliente}, sua {variavel_inexistente}")

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert "Variável desconhecida" in notification.last_error
    mock_send.assert_not_called()


async def test_send_notification_renders_template_variables():
    notification = _make_notification()
    scheduling = _make_scheduling()
    scheduling.starts_at = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    client = _make_client(name="Maria Souza", phone="5548911111111")
    service = _make_service(name="Manicure")
    template = _make_template(
        content="Olá {cliente}, seu {servico} é em {data} às {hora}"
    )

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, client, service, template]

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    sent_text = mock_send.call_args[0][1]
    assert "Maria Souza" in sent_text
    assert "Manicure" in sent_text
    assert "01/06/2026" in sent_text
    assert "11:30" in sent_text  # UTC 14:30 = BRT 11:30


async def test_dispatch_pending_dispatches_task_per_notification():
    n1 = MagicMock(id=uuid.uuid7())
    n2 = MagicMock(id=uuid.uuid7())

    mock_repo = AsyncMock(spec=SchedulingNotificationsRepository)
    mock_repo.get_pending_due.return_value = [n1, n2]

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_db = MagicMock()
    mock_db.create_session.return_value = mock_session

    with (
        patch("app.worker.notifications.db", mock_db),
        patch(
            "app.worker.notifications.SchedulingNotificationsRepository",
            return_value=mock_repo,
        ),
        patch("app.worker.notifications.send_notification") as mock_send_task,
    ):
        await _dispatch_pending()

    assert mock_send_task.delay.call_count == 2
    mock_send_task.delay.assert_any_call(str(n1.id))
    mock_send_task.delay.assert_any_call(str(n2.id))


async def test_dispatch_pending_does_nothing_when_empty():
    mock_repo = AsyncMock(spec=SchedulingNotificationsRepository)
    mock_repo.get_pending_due.return_value = []

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_db = MagicMock()
    mock_db.create_session.return_value = mock_session

    with (
        patch("app.worker.notifications.db", mock_db),
        patch(
            "app.worker.notifications.SchedulingNotificationsRepository",
            return_value=mock_repo,
        ),
        patch("app.worker.notifications.send_notification") as mock_send_task,
    ):
        await _dispatch_pending()

    mock_send_task.delay.assert_not_called()


async def test_send_notification_marks_failed_when_scheduling_not_found():
    notification = _make_notification()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.return_value = None  # scheduling not found

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert notification.last_error is not None
    assert notification.attempts == 1
    assert notification.last_attempt_at is not None
    mock_send.assert_not_called()


async def test_send_notification_marks_failed_when_related_data_not_found():
    notification = _make_notification()
    scheduling = _make_scheduling()

    mock_session = _mock_session_with_notification(notification)
    mock_session.get.side_effect = [scheduling, None, None, None]  # client/service/template missing

    with patch("app.worker.notifications.send_text") as mock_send:
        await _send_notification(notification.id, mock_session)

    assert notification.status == NotificationStatus.failed
    assert notification.last_error is not None
    assert notification.attempts == 1
    assert notification.last_attempt_at is not None
    mock_send.assert_not_called()
