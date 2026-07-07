import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.infra.repository import ClientsRepository
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.operating_hours.infra.repository import OperatingHoursRepository
from app.modules.scheduling_notifications.application.create import (
    SchedulingNotificationsCreator,
)
from app.modules.schedulings.application._authz import assert_can_write
from app.modules.schedulings.domain.enums import (
    ChangedBySource,
    SchedulingSource,
    SchedulingStatus,
)
from app.modules.schedulings.domain.exceptions import (
    SchedulingOverlapClientError,
    SchedulingOverlapUserError,
)
from app.modules.schedulings.domain.model import Scheduling, SchedulingStatusLog
from app.modules.schedulings.domain.schemas import (
    SchedulingCreate,
    SchedulingExpandedRead,
)
from app.modules.schedulings.infra.repository import SchedulingsRepository
from app.modules.services.infra.repository import ServicesRepository
from app.modules.users.domain.enums import UserRole
from app.modules.users.infra.repository import UsersRepository

_ESTABLISHMENT_TZ = ZoneInfo("America/Sao_Paulo")


class SchedulingsCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        data: SchedulingCreate,
        actor: UserActor,
        establishment_id: uuid.UUID,
        source: SchedulingSource = SchedulingSource.APP,
    ) -> SchedulingExpandedRead:
        assert_can_write(actor, establishment_id)

        is_admin = actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN})
        if not is_admin and actor.user_id != data.user_id:
            raise ForbiddenError("member só pode criar agendamento para si mesmo.")

        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            users_repo = self._uow.repository(UsersRepository)
            clients_repo = self._uow.repository(ClientsRepository)
            services_repo = self._uow.repository(ServicesRepository)
            membership_repo = self._uow.repository(MembershipRepository)
            hours_repo = self._uow.repository(OperatingHoursRepository)

            user = await users_repo.get_by_id_or_none(data.user_id)
            if user is None or not user.is_active:
                raise NotFoundError("Profissional não encontrado ou inativo.")
            membership = await membership_repo.get_by_user_and_establishment_or_none(
                data.user_id, establishment_id
            )
            if membership is None:
                raise NotFoundError("Profissional não pertence a este estabelecimento.")

            client = await clients_repo.get_by_id_or_none(data.client_id)
            if (
                client is None
                or not client.is_active
                or client.establishment_id != establishment_id
            ):
                raise NotFoundError(
                    "Cliente não encontrado, inativo ou fora do escopo."
                )

            service = await services_repo.get_by_id_or_none(data.service_id)
            if (
                service is None
                or not service.is_active
                or service.establishment_id != establishment_id
            ):
                raise NotFoundError(
                    "Serviço não encontrado, inativo ou fora do escopo."
                )

            starts_at = data.starts_at
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=UTC)

            if starts_at <= datetime.now(tz=UTC):
                raise ValidationAppError("starts_at não pode estar no passado.")

            ends_at = starts_at + timedelta(minutes=service.duration_minutes)

            await self._validate_operating_hours(
                hours_repo, establishment_id, starts_at
            )

            if await repo.has_user_overlap(data.user_id, starts_at, ends_at):
                raise SchedulingOverlapUserError()

            if await repo.has_client_overlap(data.client_id, starts_at, ends_at):
                raise SchedulingOverlapClientError()

            scheduling = Scheduling(
                establishment_id=establishment_id,
                user_id=data.user_id,
                client_id=data.client_id,
                service_id=data.service_id,
                status=SchedulingStatus.PENDING,
                source=source,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            scheduling = await repo.create(scheduling)

            log = SchedulingStatusLog(
                scheduling_id=scheduling.id,
                from_status=None,
                to_status=SchedulingStatus.PENDING,
                changed_by_source=ChangedBySource.USER,
                changed_by_user_id=actor.user_id,
            )
            logs_session = self._uow.session
            logs_session.add(log)
            await logs_session.flush()

            notifications_creator = SchedulingNotificationsCreator(self._uow)
            await notifications_creator.create_for_scheduling(scheduling)

            expanded = await repo.get_by_id_expanded(scheduling.id)
            return SchedulingExpandedRead.model_validate(expanded)

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
