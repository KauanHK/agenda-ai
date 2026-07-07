from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.scheduling_notifications.application.cancel import (
    SchedulingNotificationsCanceller,
)
from app.modules.scheduling_notifications.application.read import (
    SchedulingNotificationsReader,
)


def get_scheduling_notifications_reader(uow: UnitOfWorkDep) -> SchedulingNotificationsReader:
    return SchedulingNotificationsReader(uow=uow)


def get_scheduling_notifications_canceller(uow: UnitOfWorkDep) -> SchedulingNotificationsCanceller:
    return SchedulingNotificationsCanceller(uow=uow)


SchedulingNotificationsReaderDep = Annotated[
    SchedulingNotificationsReader, Depends(get_scheduling_notifications_reader)
]
SchedulingNotificationsCancellerDep = Annotated[
    SchedulingNotificationsCanceller, Depends(get_scheduling_notifications_canceller)
]
