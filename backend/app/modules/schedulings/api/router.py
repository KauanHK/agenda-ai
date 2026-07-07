import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.schedulings.api.deps import (
    SchedulingsCreatorDep,
    SchedulingsReaderDep,
    SchedulingsUpdaterDep,
)
from app.modules.schedulings.domain.enums import SchedulingSource, SchedulingStatus
from app.modules.schedulings.domain.filters import SchedulingFilters
from app.modules.schedulings.domain.schemas import (
    CancelSchedulingRequest,
    RescheduleRequest,
    SchedulingCreate,
    SchedulingExpandedRead,
    SchedulingRead,
    SchedulingStatusLogRead,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SchedulingRead],
)
async def list_schedulings(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: SchedulingsReaderDep,
    actor: ActorDep,
    status: SchedulingStatus | None = None,
    source: SchedulingSource | None = None,
    user_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    service_id: uuid.UUID | None = None,
    starts_at_from: str | None = None,
    starts_at_to: str | None = None,
) -> PaginatedResponse[SchedulingRead]:
    from datetime import datetime

    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        establishment_id=establishment_id,
        filters=SchedulingFilters(
            status=status,
            source=source,
            user_id=user_id,
            client_id=client_id,
            service_id=service_id,
            starts_at_from=datetime.fromisoformat(starts_at_from)
            if starts_at_from
            else None,
            starts_at_to=datetime.fromisoformat(starts_at_to) if starts_at_to else None,
        ),
    )


@router.get(
    "/{scheduling_id}",
    response_model=SchedulingExpandedRead,
)
async def get_scheduling(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    reader: SchedulingsReaderDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await reader.get_by_id(scheduling_id, actor, establishment_id)


@router.post(
    "",
    response_model=SchedulingExpandedRead,
    status_code=201,
)
async def create_scheduling(
    establishment_id: uuid.UUID,
    data: SchedulingCreate,
    creator: SchedulingsCreatorDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await creator.create(data, actor, establishment_id)


@router.post(
    "/{scheduling_id}/confirm",
    response_model=SchedulingExpandedRead,
)
async def confirm_scheduling(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    updater: SchedulingsUpdaterDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await updater.confirm(scheduling_id, actor, establishment_id)


@router.post(
    "/{scheduling_id}/cancel",
    response_model=SchedulingExpandedRead,
)
async def cancel_scheduling(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    data: CancelSchedulingRequest,
    updater: SchedulingsUpdaterDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await updater.cancel(scheduling_id, data, actor, establishment_id)


@router.post(
    "/{scheduling_id}/complete",
    response_model=SchedulingExpandedRead,
)
async def complete_scheduling(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    updater: SchedulingsUpdaterDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await updater.complete(scheduling_id, actor, establishment_id)


@router.post(
    "/{scheduling_id}/reschedule",
    response_model=SchedulingExpandedRead,
)
async def reschedule_scheduling(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    data: RescheduleRequest,
    updater: SchedulingsUpdaterDep,
    actor: ActorDep,
) -> SchedulingExpandedRead:
    return await updater.reschedule(scheduling_id, data, actor, establishment_id)


@router.get(
    "/{scheduling_id}/logs",
    response_model=PaginatedResponse[SchedulingStatusLogRead],
)
async def list_scheduling_logs(
    establishment_id: uuid.UUID,
    scheduling_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: SchedulingsReaderDep,
    actor: ActorDep,
) -> PaginatedResponse[SchedulingStatusLogRead]:
    return await reader.list_logs(scheduling_id, pagination, actor, establishment_id)
