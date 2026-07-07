import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import update as sa_update

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.scheduling_notifications.domain.enums import NotificationStatus
from app.modules.scheduling_notifications.domain.model import SchedulingNotification
from app.modules.schedulings.application._authz import (
    assert_can_admin,
    assert_can_manage,
)
from app.modules.schedulings.domain.enums import (
    ChangedBySource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.exceptions import (
    SchedulingOverlapClientError,
    SchedulingOverlapUserError,
)
from app.modules.schedulings.domain.model import Scheduling, SchedulingStatusLog
from app.modules.schedulings.domain.schemas import (
    CancelSchedulingRequest,
    RescheduleRequest,
    SchedulingExpandedRead,
)
from app.modules.schedulings.infra.repository import SchedulingsRepository

_ESTABLISHMENT_TZ = ZoneInfo("America/Sao_Paulo")

_TERMINAL_STATUSES = {SchedulingStatus.CANCELLED, SchedulingStatus.COMPLETED}


class SchedulingsUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def confirm(
        self,
        scheduling_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingExpandedRead:
        async with self._uow:
            scheduling = await self._fetch_and_scope(scheduling_id, establishment_id)
            assert_can_manage(actor, establishment_id, scheduling.user_id)

            if scheduling.status != SchedulingStatus.PENDING:
                raise ConflictError(
                    "Apenas agendamentos pendentes podem ser confirmados."
                )

            await self._transition(
                scheduling,
                to_status=SchedulingStatus.CONFIRMED,
                actor=actor,
            )
            return await self._expanded(scheduling_id)

    async def cancel(
        self,
        scheduling_id: uuid.UUID,
        data: CancelSchedulingRequest,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingExpandedRead:
        async with self._uow:
            scheduling = await self._fetch_and_scope(scheduling_id, establishment_id)
            assert_can_manage(actor, establishment_id, scheduling.user_id)

            if scheduling.status in _TERMINAL_STATUSES:
                raise ConflictError("Agendamento já está em um estado terminal.")

            scheduling.cancelled_by_type = data.cancelled_by_type
            scheduling.cancelled_by_user_id = data.cancelled_by_user_id

            await self._transition(
                scheduling,
                to_status=SchedulingStatus.CANCELLED,
                actor=actor,
            )

            await self._cancel_pending_notifications(scheduling_id)

            # TODO: enqueue Celery tasks for cancellation notification and Google Calendar

            return await self._expanded(scheduling_id)

    async def complete(
        self,
        scheduling_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingExpandedRead:
        assert_can_admin(actor, establishment_id)

        async with self._uow:
            scheduling = await self._fetch_and_scope(scheduling_id, establishment_id)

            if scheduling.status != SchedulingStatus.CONFIRMED:
                raise ConflictError(
                    "Apenas agendamentos confirmados podem ser concluídos."
                )

            await self._transition(
                scheduling,
                to_status=SchedulingStatus.COMPLETED,
                actor=actor,
            )
            return await self._expanded(scheduling_id)

    async def reschedule(
        self,
        scheduling_id: uuid.UUID,
        data: RescheduleRequest,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingExpandedRead:
        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            hours_repo = self._uow.repository(OperatingHoursRepository)

            scheduling = await self._fetch_and_scope(scheduling_id, establishment_id)
            assert_can_manage(actor, establishment_id, scheduling.user_id)

            if scheduling.status in _TERMINAL_STATUSES:
                raise ConflictError(
                    "Não é possível reagendar um agendamento em estado terminal."
                )

            new_starts_at = data.starts_at
            if new_starts_at.tzinfo is None:
                new_starts_at = new_starts_at.replace(tzinfo=UTC)

            if new_starts_at <= datetime.now(tz=UTC):
                raise ValidationAppError("O novo starts_at não pode estar no passado.")

            service_duration = await self._get_service_duration(scheduling.service_id)
            new_ends_at = new_starts_at + timedelta(minutes=service_duration)

            await self._validate_operating_hours(
                hours_repo, establishment_id, new_starts_at
            )

            if await repo.has_user_overlap(
                scheduling.user_id, new_starts_at, new_ends_at, exclude_id=scheduling_id
            ):
                raise SchedulingOverlapUserError()

            if await repo.has_client_overlap(
                scheduling.client_id,
                new_starts_at,
                new_ends_at,
                exclude_id=scheduling_id,
            ):
                raise SchedulingOverlapClientError()

            scheduling.starts_at = new_starts_at
            scheduling.ends_at = new_ends_at
            await repo.update(scheduling)

            return await self._expanded(scheduling_id)

    async def _fetch_and_scope(
        self,
        scheduling_id: uuid.UUID,
        establishment_id: uuid.UUID,
    ) -> Scheduling:
        repo = self._uow.repository(SchedulingsRepository)
        scheduling = await repo.get_by_id(scheduling_id)
        if scheduling.establishment_id != establishment_id:
            raise NotFoundError("Agendamento não encontrado.")
        return scheduling

    async def _transition(
        self,
        scheduling: Scheduling,
        to_status: SchedulingStatus,
        actor: UserActor,
    ) -> None:
        repo = self._uow.repository(SchedulingsRepository)
        from_status = scheduling.status
        scheduling.status = to_status
        await repo.update(scheduling)

        log = SchedulingStatusLog(
            scheduling_id=scheduling.id,
            from_status=from_status,
            to_status=to_status,
            changed_by_source=ChangedBySource.USER,
            changed_by_user_id=actor.user_id,
        )
        self._uow.session.add(log)
        await self._uow.session.flush()

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

    async def _expanded(self, scheduling_id: uuid.UUID) -> SchedulingExpandedRead:
        repo = self._uow.repository(SchedulingsRepository)
        scheduling = await repo.get_by_id_expanded(scheduling_id)
        return SchedulingExpandedRead.model_validate(scheduling)

    async def _get_service_duration(self, service_id: uuid.UUID) -> int:
        from app.modules.services.infra.repository import ServicesRepository

        services_repo = self._uow.repository(ServicesRepository)
        service = await services_repo.get_by_id(service_id)
        return service.duration_minutes

    async def _validate_operating_hours(
        self,
        hours_repo: OperatingHoursRepository,
        establishment_id: uuid.UUID,
        starts_at: datetime,
    ) -> None:
        starts_local = starts_at.astimezone(_ESTABLISHMENT_TZ)
        weekday = starts_local.weekday()
        time_of_day = starts_local.time().replace(tzinfo=None)

        hours = await hours_repo.list_by_establishment(establishment_id)
        operating = next((h for h in hours if h.weekday == weekday), None)

        if operating is None:
            raise ValidationAppError(
                "Estabelecimento não funciona neste dia da semana."
            )

        if not (operating.start_time <= time_of_day < operating.end_time):
            raise ValidationAppError("starts_at fora do horário de funcionamento.")
