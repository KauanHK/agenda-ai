import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.domain.enums import TemplateType
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository
from app.modules.scheduling_notifications.application.create import (
    SchedulingNotificationsCreator,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.schedulings.domain.enums import SchedulingSource, SchedulingStatus
from app.modules.schedulings.domain.model import Scheduling


def make_template(establishment_id: uuid.UUID, minutes_before: int = 60) -> MessagingTemplate:
    return MessagingTemplate(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        name="Lembrete",
        content="Olá {cliente}, seu {servico} é em {data} às {hora}",
        type=TemplateType.REMINDER,
        is_active=True,
        minutes_before=minutes_before,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_scheduling(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    starts_at: datetime,
) -> Scheduling:
    return Scheduling(
        id=uuid.uuid7(),
        establishment_id=establishment_id,
        user_id=uuid.uuid7(),
        client_id=uuid.uuid7(),
        service_id=service_id,
        status=SchedulingStatus.PENDING,
        source=SchedulingSource.APP,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
    )


async def test_create_for_scheduling_inserts_one_notification_per_template():
    establishment_id = uuid.uuid7()
    service_id = uuid.uuid7()
    starts_at = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    scheduling = make_scheduling(establishment_id, service_id, starts_at)

    template_60 = make_template(establishment_id, minutes_before=60)
    template_1440 = make_template(establishment_id, minutes_before=1440)

    mock_templates_repo = AsyncMock(spec=MessagingTemplatesRepository)
    mock_templates_repo.get_active_templates_for_service.return_value = [
        template_60,
        template_1440,
    ]

    mock_session = MagicMock()
    mock_session.flush = AsyncMock()
    mock_uow = MagicMock(spec=UnitOfWork)
    mock_uow.session = mock_session
    mock_uow.repository.return_value = mock_templates_repo

    creator = SchedulingNotificationsCreator(mock_uow)
    notifications = await creator.create_for_scheduling(scheduling)

    assert len(notifications) == 2
    assert mock_session.add.call_count == 2
    mock_session.flush.assert_called_once()
    assert notifications[0].scheduled_at == starts_at - timedelta(minutes=60)
    assert notifications[1].scheduled_at == starts_at - timedelta(minutes=1440)
    assert all(n.status == NotificationStatus.pending for n in notifications)
    assert all(n.scheduling_id == scheduling.id for n in notifications)
    assert all(n.establishment_id == establishment_id for n in notifications)
    assert notifications[0].template_id == template_60.id
    assert notifications[1].template_id == template_1440.id


async def test_create_for_scheduling_creates_nothing_when_no_templates():
    establishment_id = uuid.uuid7()
    service_id = uuid.uuid7()
    starts_at = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    scheduling = make_scheduling(establishment_id, service_id, starts_at)

    mock_templates_repo = AsyncMock(spec=MessagingTemplatesRepository)
    mock_templates_repo.get_active_templates_for_service.return_value = []

    mock_session = MagicMock()
    mock_session.flush = AsyncMock()
    mock_uow = MagicMock(spec=UnitOfWork)
    mock_uow.session = mock_session
    mock_uow.repository.return_value = mock_templates_repo

    creator = SchedulingNotificationsCreator(mock_uow)
    notifications = await creator.create_for_scheduling(scheduling)

    assert notifications == []
    mock_session.add.assert_not_called()
    mock_session.flush.assert_not_called()
