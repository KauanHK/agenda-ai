import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.services.api.deps import (
    ServicesActivatorDep,
    ServicesCreatorDep,
    ServicesDeleterDep,
    ServicesQueryParamsDep,
    ServicesReaderDep,
    ServicesUpdaterDep,
)
from app.modules.services.domain.schemas import (
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)

router = APIRouter()


@router.get("")
async def list_services(
    establishment_id: uuid.UUID,
    query_params: ServicesQueryParamsDep,
    pagination: PaginationParamsDep,
    reader: ServicesReaderDep,
) -> PaginatedResponse[ServiceRead]:
    return await reader.paginate(
        pagination=pagination,
        filters=query_params.to_filters(
            establishment_id=establishment_id,
        ),
    )


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    reader: ServicesReaderDep,
    actor: ActorDep,
) -> ServiceRead:
    return await reader.get_by_id(service_id, actor, establishment_id)


@router.post("", response_model=ServiceRead, status_code=201)
async def create_service(
    establishment_id: uuid.UUID,
    data: ServiceCreate,
    creator: ServicesCreatorDep,
    actor: ActorDep,
) -> ServiceRead:
    return await creator.create(data, actor, establishment_id)


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    data: ServiceUpdate,
    updater: ServicesUpdaterDep,
    actor: ActorDep,
) -> ServiceRead:
    return await updater.update(service_id, data, actor, establishment_id)


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    deleter: ServicesDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(service_id, actor, establishment_id)


@router.post("/{service_id}/activate", response_model=ServiceRead)
async def activate_service(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    activator: ServicesActivatorDep,
    actor: ActorDep,
) -> ServiceRead:
    return await activator.activate(service_id, actor, establishment_id)


@router.post("/{service_id}/deactivate", response_model=ServiceRead)
async def deactivate_service(
    establishment_id: uuid.UUID,
    service_id: uuid.UUID,
    activator: ServicesActivatorDep,
    actor: ActorDep,
) -> ServiceRead:
    return await activator.deactivate(service_id, actor, establishment_id)
