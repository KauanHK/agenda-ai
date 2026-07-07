from datetime import timedelta

from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.infra.repository import MessagingTemplatesRepository
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.schedulings.domain.model import Scheduling


class SchedulingNotificationsCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create_for_scheduling(self, scheduling: Scheduling) -> list[SchedulingNotification]:
        templates_repo = self._uow.repository(MessagingTemplatesRepository)
        templates = await templates_repo.get_active_templates_for_service(
            scheduling.service_id, scheduling.establishment_id
        )

        notifications: list[SchedulingNotification] = []
        for template in templates:
            if template.minutes_before is None:
                continue
            scheduled_at = scheduling.starts_at - timedelta(minutes=template.minutes_before)
            notification = SchedulingNotification(
                establishment_id=scheduling.establishment_id,
                scheduling_id=scheduling.id,
                template_id=template.id,
                scheduled_at=scheduled_at,
                status=NotificationStatus.pending,
            )
            self._uow.session.add(notification)
            notifications.append(notification)

        if notifications:
            await self._uow.session.flush()
        return notifications
