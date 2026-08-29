import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.scheduling_notifications.application.dtos.filters import (
    SchedulingNotificationFilters,
)
from app.modules.scheduling_notifications.application.use_cases.read import (
    SchedulingNotificationsReader,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from tests.modules.scheduling_notifications.application.use_cases.conftest import (
    make_notification,
)


async def test_get_by_id_returns_notification(
    uow, notifications_repo, admin_user, establishment_id
):
    notification = make_notification(establishment_id)
    notifications_repo.get_by_id.return_value = notification

    result = await SchedulingNotificationsReader(uow).get_by_id(
        notification.id, admin_user, establishment_id
    )

    assert result == notification


async def test_get_by_id_raises_not_found_for_other_tenant(
    uow, notifications_repo, admin_user, establishment_id
):
    notifications_repo.get_by_id.return_value = make_notification(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Notificação não encontrada"):
        await SchedulingNotificationsReader(uow).get_by_id(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_get_by_id_allowed_for_member(
    uow, notifications_repo, member_user, establishment_id
):
    notification = make_notification(establishment_id)
    notifications_repo.get_by_id.return_value = notification

    result = await SchedulingNotificationsReader(uow).get_by_id(
        notification.id, member_user, establishment_id
    )

    assert result == notification


async def test_paginate_scopes_filters_to_establishment(
    uow, notifications_repo, admin_user, establishment_id
):
    notifications_repo.paginate.return_value = Page(
        items=[], total=0, page=1, page_size=10
    )
    scheduling_id = uuid.uuid7()

    await SchedulingNotificationsReader(uow).paginate(
        PageParams(page=1, page_size=10),
        admin_user,
        establishment_id,
        filters=SchedulingNotificationFilters(
            establishment_id=uuid.uuid7(),  # deve ser sobrescrito
            scheduling_id=scheduling_id,
            status=NotificationStatus.pending,
        ),
    )

    sent: SchedulingNotificationFilters = notifications_repo.paginate.call_args.kwargs[
        "filters"
    ]
    assert sent.establishment_id == establishment_id
    assert sent.scheduling_id == scheduling_id
    assert sent.status == NotificationStatus.pending


async def test_paginate_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await SchedulingNotificationsReader(uow).paginate(
            PageParams(page=1, page_size=10), global_admin_user, establishment_id
        )
