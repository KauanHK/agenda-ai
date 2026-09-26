import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.schedulings.application._authz import (
    assert_can_access,
    assert_can_manage,
)
from app.modules.schedulings.domain.filters import SchedulingFilters
from app.modules.schedulings.domain.model import Scheduling
from app.modules.schedulings.domain.schemas import (
    SchedulingExpandedRead,
    SchedulingRead,
    SchedulingStatusLogRead,
)
from app.modules.schedulings.infra.repository import (
    SchedulingsRepository,
    SchedulingStatusLogsRepository,
)
from app.modules.users.domain.enums import UserRole


class SchedulingsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: SchedulingFilters | None = None,
    ) -> PaginatedResponse[SchedulingRead]:
        assert_can_access(actor, establishment_id)

        filters = filters or SchedulingFilters()
        is_admin = actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN})

        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)

            scoped = SchedulingFilters(
                establishment_id=establishment_id,
                status=filters.status,
                source=filters.source,
                user_id=filters.user_id if is_admin else actor.user_id,
                client_id=filters.client_id,
                service_id=filters.service_id,
                starts_at_from=filters.starts_at_from,
                starts_at_to=filters.starts_at_to,
            )

            items = await repo.list(pagination=pagination, filters=scoped)
            total = await repo.count(filters=scoped)

            return build_paginated_response(
                items=[SchedulingRead.model_validate(s) for s in items],
                total=total,
                params=pagination,
            )

    async def get_by_id(
        self,
        scheduling_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> SchedulingExpandedRead:
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            scheduling = await repo.get_by_id_expanded(scheduling_id)
            if scheduling is None:
                raise NotFoundError("Agendamento não encontrado.")
            self._assert_scope(scheduling, establishment_id)
            assert_can_manage(actor, establishment_id, scheduling.user_id)
            return SchedulingExpandedRead.model_validate(scheduling)

    async def list_logs(
        self,
        scheduling_id: uuid.UUID,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> PaginatedResponse[SchedulingStatusLogRead]:
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            scheduling = await repo.get_by_id(scheduling_id)
            self._assert_scope(scheduling, establishment_id)
            assert_can_manage(actor, establishment_id, scheduling.user_id)

            logs_repo = self._uow.repository(SchedulingStatusLogsRepository)
            logs = await logs_repo.list_by_scheduling(scheduling_id, pagination)
            total = await logs_repo.count_by_scheduling(scheduling_id)

            return build_paginated_response(
                items=[SchedulingStatusLogRead.model_validate(log) for log in logs],
                total=total,
                params=pagination,
            )

    def _assert_scope(
        self, scheduling: Scheduling, establishment_id: uuid.UUID
    ) -> None:
        if scheduling.establishment_id != establishment_id:
            raise NotFoundError("Agendamento não encontrado.")
