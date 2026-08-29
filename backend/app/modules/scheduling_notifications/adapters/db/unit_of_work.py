from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.scheduling_notifications.adapters.db.repository import (
    SchedulingNotificationsRepository,
)


class SchedulingNotificationsUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """Inicializa a unidade de trabalho de notificações de agendamento."""

        super().__init__(session_factory=session_factory)
        self._scheduling_notifications: SchedulingNotificationsRepository | None = None

    @property
    def scheduling_notifications(self) -> SchedulingNotificationsRepository:
        """Repositório de notificações de agendamento."""
        if self._scheduling_notifications is None:
            raise RuntimeError(
                "Repositório de notificações de agendamento não inicializado."
            )
        return self._scheduling_notifications

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._scheduling_notifications = SchedulingNotificationsRepository(
            self.session
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._scheduling_notifications = None
