import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.modules.scheduling_notifications.application.use_cases.cancel import (
    SchedulingNotificationsCanceller,
)
from app.modules.scheduling_notifications.domain.entities import (
    UpdateSchedulingNotification,
)
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from tests.modules.scheduling_notifications.application.use_cases.conftest import (
    make_notification,
)


async def test_cancel_sets_status_cancelled(
    uow, notifications_repo, admin_user, establishment_id
):
    notification = make_notification(establishment_id)
    notifications_repo.get_by_id.return_value = notification
    notifications_repo.update.return_value = make_notification(
        establishment_id, status=NotificationStatus.cancelled
    )

    result = await SchedulingNotificationsCanceller(uow).cancel(
        notification.id, admin_user, establishment_id
    )

    assert result.status == NotificationStatus.cancelled
    sent: UpdateSchedulingNotification = notifications_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.status == NotificationStatus.cancelled


async def test_cancel_raises_not_found_for_other_tenant(
    uow, notifications_repo, admin_user, establishment_id
):
    notifications_repo.get_by_id.return_value = make_notification(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Notificação não encontrada"):
        await SchedulingNotificationsCanceller(uow).cancel(
            uuid.uuid7(), admin_user, establishment_id
        )


@pytest.mark.parametrize(
    "status",
    [NotificationStatus.sent, NotificationStatus.cancelled, NotificationStatus.failed],
)
async def test_cancel_rejects_non_pending(
    uow, notifications_repo, admin_user, establishment_id, status
):
    notifications_repo.get_by_id.return_value = make_notification(
        establishment_id, status=status
    )

    with pytest.raises(ValidationAppError, match="pendentes"):
        await SchedulingNotificationsCanceller(uow).cancel(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_cancel_forbidden_for_member(uow, member_user, establishment_id):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await SchedulingNotificationsCanceller(uow).cancel(
            uuid.uuid7(), member_user, establishment_id
        )


async def test_cancel_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await SchedulingNotificationsCanceller(uow).cancel(
            uuid.uuid7(), global_admin_user, establishment_id
        )
