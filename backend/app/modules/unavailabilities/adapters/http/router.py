import uuid
from datetime import datetime

from fastapi import APIRouter, Response

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.params import Page
from app.core.pagination.schemas import (
    PaginatedResponse,
    build_paginated_response_from_page,
)
from app.modules.unavailabilities.adapters.http.dependencies import (
    UnavailabilitiesUnitOfWorkDep,
)
from app.modules.unavailabilities.adapters.http.schemas import (
    UnavailabilityCreate,
    UnavailabilityRead,
    UnavailabilityUpdate,
)
from app.modules.unavailabilities.application.dtos.commands import (
    CreateUnavailabilityCommand,
    UpdateUnavailabilityCommand,
)
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.application.use_cases.create import (
    UnavailabilitiesCreator,
)
from app.modules.unavailabilities.application.use_cases.delete import (
    UnavailabilitiesDeleter,
)
from app.modules.unavailabilities.application.use_cases.read import (
    UnavailabilitiesReader,
)
from app.modules.unavailabilities.application.use_cases.update import (
    UnavailabilitiesUpdater,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UnavailabilityRead],
)
async def list_unavailabilities(
    establishment_id: uuid.UUID,
    page_params: PageParamsDep,
    uow: UnavailabilitiesUnitOfWorkDep,
    actor: ActorDep,
    starts_at_from: datetime | None = None,
    starts_at_to: datetime | None = None,
) -> PaginatedResponse[UnavailabilityRead]:
    page = await UnavailabilitiesReader(uow=uow).paginate(
        page_params=page_params,
        actor=actor,
        establishment_id=establishment_id,
        filters=UnavailabilityFilters(
            starts_at_from=starts_at_from, starts_at_to=starts_at_to
        ),
    )
    return build_paginated_response_from_page(
        Page(
            items=[UnavailabilityRead.model_validate(u.to_dict()) for u in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
    )


@router.get(
    "/{unavailability_id}",
    response_model=UnavailabilityRead,
)
async def get_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    uow: UnavailabilitiesUnitOfWorkDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    unavailability = await UnavailabilitiesReader(uow=uow).get_by_id(
        unavailability_id, actor, establishment_id
    )
    return UnavailabilityRead.model_validate(unavailability.to_dict())


@router.post(
    "",
    response_model=UnavailabilityRead,
    status_code=201,
)
async def create_unavailability(
    establishment_id: uuid.UUID,
    data: UnavailabilityCreate,
    uow: UnavailabilitiesUnitOfWorkDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    unavailability = await UnavailabilitiesCreator(uow=uow).create(
        CreateUnavailabilityCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return UnavailabilityRead.model_validate(unavailability.to_dict())


@router.patch(
    "/{unavailability_id}",
    response_model=UnavailabilityRead,
)
async def update_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    data: UnavailabilityUpdate,
    uow: UnavailabilitiesUnitOfWorkDep,
    actor: ActorDep,
) -> UnavailabilityRead:
    unavailability = await UnavailabilitiesUpdater(uow=uow).update(
        unavailability_id,
        UpdateUnavailabilityCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return UnavailabilityRead.model_validate(unavailability.to_dict())


@router.delete("/{unavailability_id}", status_code=204)
async def delete_unavailability(
    establishment_id: uuid.UUID,
    unavailability_id: uuid.UUID,
    uow: UnavailabilitiesUnitOfWorkDep,
    actor: ActorDep,
) -> Response:
    await UnavailabilitiesDeleter(uow=uow).delete(
        unavailability_id, actor, establishment_id
    )
    return Response(status_code=204)
