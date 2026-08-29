from types import TracebackType
from typing import Protocol, Self

from app.modules.scheduling_notifications.application.ports.repositories import (
    SchedulingNotificationsRepositoryProtocol,
)


class SchedulingNotificationsUnitOfWorkProtocol(Protocol):
    @property
    def scheduling_notifications(self) -> SchedulingNotificationsRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
