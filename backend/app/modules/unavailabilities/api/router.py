import uuid
from datetime import datetime

from fastapi import APIRouter, Response

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.unavailabilities.api.deps import (
    UnavailabilitiesCreatorDep,
    UnavailabilitiesDeleterDep,
    UnavailabilitiesReaderDep,
    UnavailabilitiesUpdaterDep,
)
from app.modules.unavailabilities.domain.filters import UnavailabilityFilters
from app.modules.unavailabilities.domain.schemas import (
    UnavailabilityCreate,
    UnavailabilityRead,
    UnavailabilityUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UnavailabilityRead],
)
async def list_unavailabilities(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: UnavailabilitiesReaderDep,
    actor: ActorDep,
    starts_at_from: datetime | None = None,
    starts_at_to: datetime | None = None,
) -> PaginatedResponse[UnavailabilityRead]:
    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        establishment_id=establishment_id,
        filters=UnavailabilityFilters(
            starts_at_from=starts_at_from, starts_at_to=starts_at_to
        ),
    )


@router.get(
    "/{unavailability_id}",
    response_model=UnavailabilityRead,
)
async def get_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    reader: UnavailabilitiesReaderDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    return await reader.get_by_id(unavailability_id, actor, establishment_id)


@router.post(
    "",
    response_model=UnavailabilityRead,
    status_code=201,
)
async def create_unavailability(
    establishment_id: uuid.UUID,
    data: UnavailabilityCreate,
    creator: UnavailabilitiesCreatorDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    return await creator.create(data, actor, establishment_id)


@router.patch(
    "/{unavailability_id}",
    response_model=UnavailabilityRead,
)
async def update_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    data: UnavailabilityUpdate,
    updater: UnavailabilitiesUpdaterDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    return await updater.update(unavailability_id, data, actor, establishment_id)


@router.delete("/{unavailability_id}", status_code=204)
async def delete_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    deleter: UnavailabilitiesDeleterDep,
    actor: ActorDep,
) -> Response:
    await deleter.delete(unavailability_id, actor, establishment_id)
    return Response(status_code=204)
