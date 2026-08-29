import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends

from app.modules.scheduling_notifications.adapters.db.factories import (
    make_unit_of_work,
)
from app.modules.scheduling_notifications.adapters.db.unit_of_work import (
    SchedulingNotificationsUnitOfWork,
)
from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus

SchedulingNotificationsUnitOfWorkDep = Annotated[
    SchedulingNotificationsUnitOfWork, Depends(make_unit_of_work)
]


def get_pagination_filters(
    scheduling_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    status: NotificationStatus | None = None,
    sent_at_from: datetime | None = None,
    sent_at_to: datetime | None = None,
) -> SchedulingNotificationFilters:
    """Dependência para obter os filtros de paginação nos query params."""

    return SchedulingNotificationFilters(
        scheduling_id=scheduling_id,
        template_id=template_id,
        status=status,
        sent_at_from=sent_at_from,
        sent_at_to=sent_at_to,
    )


PaginationFiltersDep = Annotated[
    SchedulingNotificationFilters, Depends(get_pagination_filters)
]
