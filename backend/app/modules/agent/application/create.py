import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.agent.actors import ClientAgentActor
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.scheduling_notifications.application.create import (
    SchedulingNotificationsCreator,
)
from app.modules.schedulings.domain.enums import (
    ChangedBySource,
    SchedulingSource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.exceptions import (
    SchedulingOverlapClientError,
)
from app.modules.schedulings.domain.model import Scheduling, SchedulingStatusLog
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository

_ESTABLISHMENT_TZ = ZoneInfo("America/Sao_Paulo")


class AgentSchedulingsCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        actor: ClientAgentActor,
        service_id: uuid.UUID,
        starts_at: datetime,
    ) -> dict:
        async with self._uow:
            services_repo = self._uow.repository(ServicesRepository)
            hours_repo = self._uow.repository(OperatingHoursRepository)
            membership_repo = self._uow.repository(MembershipRepository)
            scheduling_repo = self._uow.repository(SchedulingsRepository)

            service = await services_repo.get_by_id_or_none(service_id)
            if (
                service is None
                or not service.is_active
                or service.establishment_id != actor.establishment_id
            ):
                raise NotFoundError("Serviço não encontrado.")

            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=UTC)

            if starts_at <= datetime.now(UTC):
                raise ValidationAppError("O horário não pode estar no passado.")

            await self._validate_operating_hours(
                hours_repo, actor.establishment_id, starts_at
            )

            ends_at = starts_at + timedelta(minutes=service.duration_minutes)

            memberships = await membership_repo.list_all_by_establishment(
                actor.establishment_id
            )
            user_ids = [m.user_id for m in memberships]
            if not user_ids:
                raise ValidationAppError("Nenhum profissional disponível.")

            assigned_user_id: uuid.UUID | None = None
            for uid in user_ids:
                if not await scheduling_repo.has_user_overlap(uid, starts_at, ends_at):
                    assigned_user_id = uid
                    break

            if assigned_user_id is None:
                raise ValidationAppError("Nenhum profissional disponível neste horário.")

            if await scheduling_repo.has_client_overlap(actor.client_id, starts_at, ends_at):
                raise SchedulingOverlapClientError()

            scheduling = Scheduling(
                establishment_id=actor.establishment_id,
                user_id=assigned_user_id,
                client_id=actor.client_id,
                service_id=service_id,
                status=SchedulingStatus.PENDING,
                source=SchedulingSource.WHATSAPP,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            scheduling = await scheduling_repo.create(scheduling)

            log = SchedulingStatusLog(
                scheduling_id=scheduling.id,
                from_status=None,
                to_status=SchedulingStatus.PENDING,
                changed_by_source=ChangedBySource.CLIENT,
                changed_by_user_id=None,
            )
            self._uow.session.add(log)
            await self._uow.session.flush()

            notifications_creator = SchedulingNotificationsCreator(self._uow)
            await notifications_creator.create_for_scheduling(scheduling)

            return {
                "scheduling_id": str(scheduling.id),
                "starts_at": scheduling.starts_at.isoformat(),
                "ends_at": scheduling.ends_at.isoformat(),
                "service_name": service.name,
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
