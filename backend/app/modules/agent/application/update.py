import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.agent.actors import ClientAgentActor
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.schedulings.domain.enums import SchedulingStatus
from app.modules.schedulings.domain.exceptions import (
    SchedulingOverlapClientError,
    SchedulingOverlapUserError,
)
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository

_ESTABLISHMENT_TZ = ZoneInfo("America/Sao_Paulo")
_TERMINAL_STATUSES = {SchedulingStatus.CANCELLED, SchedulingStatus.COMPLETED}


class AgentSchedulingsRescheduler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def reschedule(
        self,
        actor: ClientAgentActor,
        scheduling_id: uuid.UUID,
        new_starts_at: datetime,
    ) -> dict:
        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            hours_repo = self._uow.repository(OperatingHoursRepository)
            services_repo = self._uow.repository(ServicesRepository)

            scheduling = await repo.get_by_id(scheduling_id)

            if scheduling.establishment_id != actor.establishment_id:
                raise NotFoundError("Agendamento não encontrado.")
            if scheduling.client_id != actor.client_id:
                raise NotFoundError("Agendamento não encontrado.")

            if scheduling.status in _TERMINAL_STATUSES:
                raise ConflictError("Não é possível reagendar um agendamento em estado terminal.")

            if new_starts_at.tzinfo is None:
                new_starts_at = new_starts_at.replace(tzinfo=UTC)

            if new_starts_at <= datetime.now(UTC):
                raise ValidationAppError("O novo horário não pode estar no passado.")

            service = await services_repo.get_by_id(scheduling.service_id)
            new_ends_at = new_starts_at + timedelta(minutes=service.duration_minutes)

            await self._validate_operating_hours(
                hours_repo, actor.establishment_id, new_starts_at
            )

            if await repo.has_user_overlap(
                scheduling.user_id, new_starts_at, new_ends_at, exclude_id=scheduling_id
            ):
                raise SchedulingOverlapUserError()

            if await repo.has_client_overlap(
                actor.client_id, new_starts_at, new_ends_at, exclude_id=scheduling_id
            ):
                raise SchedulingOverlapClientError()

            scheduling.starts_at = new_starts_at
            scheduling.ends_at = new_ends_at
            await repo.update(scheduling)

            return {
                "scheduling_id": str(scheduling.id),
                "starts_at": scheduling.starts_at.isoformat(),
                "ends_at": scheduling.ends_at.isoformat(),
            }

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
            raise ValidationAppError("Estabelecimento não funciona neste dia da semana.")

        if not (operating.start_time <= time_of_day < operating.end_time):
            raise ValidationAppError("Horário fora do funcionamento do estabelecimento.")
