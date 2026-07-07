import uuid
from datetime import datetime

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.scheduling_notifications.api.deps import (
    SchedulingNotificationsCancellerDep,
    SchedulingNotificationsReaderDep,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.schemas import (
    SchedulingNotificationRead,
)

router = APIRouter()


@router.get(
    "/notifications",
    response_model=PaginatedResponse[SchedulingNotificationRead],
)
async def list_scheduling_notifications(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: SchedulingNotificationsReaderDep,
    actor: ActorDep,
    scheduling_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    status: NotificationStatus | None = None,
    sent_at_from: datetime | None = None,
    sent_at_to: datetime | None = None,
) -> PaginatedResponse[SchedulingNotificationRead]:
    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        establishment_id=establishment_id,
        filters=SchedulingNotificationFilters(
            scheduling_id=scheduling_id,
            template_id=template_id,
            status=status,
            sent_at_from=sent_at_from,
            sent_at_to=sent_at_to,
        ),
    )


@router.get(
    "/notifications/{notification_id}",
    response_model=SchedulingNotificationRead,
)
async def get_scheduling_notification(
    establishment_id: uuid.UUID,
    notification_id: uuid.UUID,
    reader: SchedulingNotificationsReaderDep,
    actor: ActorDep,
) -> SchedulingNotificationRead:
    return await reader.get_by_id(notification_id, actor, establishment_id)


@router.post(
    "/notifications/{notification_id}/cancel",
    response_model=SchedulingNotificationRead,
)
async def cancel_scheduling_notification(
    establishment_id: uuid.UUID,
    notification_id: uuid.UUID,
    canceller: SchedulingNotificationsCancellerDep,
    actor: ActorDep,
) -> SchedulingNotificationRead:
    return await canceller.cancel(notification_id, actor, establishment_id)
