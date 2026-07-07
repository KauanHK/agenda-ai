import uuid

from sqlalchemy import update as sa_update

from app.core.exceptions import ConflictError, NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.agent.actors import ClientAgentActor
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.schedulings.domain.enums import (
    CancelledByType,
    ChangedBySource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.model import SchedulingStatusLog
from app.modules.schedulings.infra.repository import SchedulingsRepository

_TERMINAL_STATUSES = {SchedulingStatus.CANCELLED, SchedulingStatus.COMPLETED}


class AgentSchedulingsCanceller:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def cancel(
        self,
        actor: ClientAgentActor,
        scheduling_id: uuid.UUID,
    ) -> dict:
        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)

            scheduling = await repo.get_by_id(scheduling_id)

            if scheduling.establishment_id != actor.establishment_id:
                raise NotFoundError("Agendamento não encontrado.")
            if scheduling.client_id != actor.client_id:
                raise NotFoundError("Agendamento não encontrado.")

            if scheduling.status in _TERMINAL_STATUSES:
                raise ConflictError("Agendamento já está em um estado terminal.")

            from_status = scheduling.status
            scheduling.status = SchedulingStatus.CANCELLED
            scheduling.cancelled_by_type = CancelledByType.CLIENT
            scheduling.cancelled_by_user_id = None
            await repo.update(scheduling)

            log = SchedulingStatusLog(
                scheduling_id=scheduling.id,
                from_status=from_status,
                to_status=SchedulingStatus.CANCELLED,
                changed_by_source=ChangedBySource.CLIENT,
                changed_by_user_id=None,
            )
            self._uow.session.add(log)
            await self._uow.session.flush()

            await self._cancel_pending_notifications(scheduling_id)

            return {"scheduling_id": str(scheduling.id), "cancelled": True}

    async def _cancel_pending_notifications(self, scheduling_id: uuid.UUID) -> None:
        stmt = (
            sa_update(SchedulingNotification)
            .where(
                SchedulingNotification.scheduling_id == scheduling_id,
                SchedulingNotification.status == NotificationStatus.pending,
            )
            .values(status=NotificationStatus.cancelled)
        )
        await self._uow.session.execute(stmt)
