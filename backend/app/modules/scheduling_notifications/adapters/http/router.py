import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.params import Page
from app.core.pagination.schemas import (
    PaginatedResponse,
    build_paginated_response_from_page,
)
from app.modules.scheduling_notifications.adapters.http.dependencies import (
    PaginationFiltersDep,
    SchedulingNotificationsUnitOfWorkDep,
)
from app.modules.scheduling_notifications.adapters.http.schemas import (
    SchedulingNotificationRead,
)
from app.modules.scheduling_notifications.application.use_cases.cancel import (
    SchedulingNotificationsCanceller,
)
from app.modules.scheduling_notifications.application.use_cases.read import (
    SchedulingNotificationsReader,
)

router = APIRouter()


@router.get(
    "/notifications",
    response_model=PaginatedResponse[SchedulingNotificationRead],
)
async def list_scheduling_notifications(
    establishment_id: uuid.UUID,
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: SchedulingNotificationsUnitOfWorkDep,
    actor: ActorDep,
) -> PaginatedResponse[SchedulingNotificationRead]:
    page = await SchedulingNotificationsReader(uow=uow).paginate(
        page_params=page_params,
        actor=actor,
        establishment_id=establishment_id,
        filters=filters,
    )
    return build_paginated_response_from_page(
        Page(
            items=[
                SchedulingNotificationRead.model_validate(n.to_dict())
                for n in page.items
            ],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
    )


@router.get(
    "/notifications/{notification_id}",
    response_model=SchedulingNotificationRead,
)
async def get_scheduling_notification(
    establishment_id: uuid.UUID,
    notification_id: uuid.UUID,
    uow: SchedulingNotificationsUnitOfWorkDep,
    actor: ActorDep,
) -> SchedulingNotificationRead:
    notification = await SchedulingNotificationsReader(uow=uow).get_by_id(
        notification_id, actor, establishment_id
    )
    return SchedulingNotificationRead.model_validate(notification.to_dict())


@router.post(
    "/notifications/{notification_id}/cancel",
    response_model=SchedulingNotificationRead,
)
async def cancel_scheduling_notification(
    establishment_id: uuid.UUID,
    notification_id: uuid.UUID,
    uow: SchedulingNotificationsUnitOfWorkDep,
    actor: ActorDep,
) -> SchedulingNotificationRead:
    notification = await SchedulingNotificationsCanceller(uow=uow).cancel(
        notification_id, actor, establishment_id
    )
    return SchedulingNotificationRead.model_validate(notification.to_dict())
