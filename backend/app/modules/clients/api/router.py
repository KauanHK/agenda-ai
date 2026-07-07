import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.clients.api.deps import (
    ClientsActivatorDep,
    ClientsCreatorDep,
    ClientsDeleterDep,
    ClientsReaderDep,
    ClientsUpdaterDep,
)
from app.modules.clients.domain.filters import ClientFilters
from app.modules.clients.domain.schemas import ClientCreate, ClientRead, ClientUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ClientRead])
async def list_clients(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: ClientsReaderDep,
    actor: ActorDep,
    q: str | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse[ClientRead]:
    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        establishment_id=establishment_id,
        filters=ClientFilters(q=q, is_active=is_active),
    )


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    reader: ClientsReaderDep,
    actor: ActorDep,
) -> ClientRead:
    return await reader.get_by_id(client_id, actor, establishment_id)


@router.post("", response_model=ClientRead, status_code=201)
async def create_client(
    establishment_id: uuid.UUID,
    data: ClientCreate,
    creator: ClientsCreatorDep,
    actor: ActorDep,
) -> ClientRead:
    return await creator.create(data, actor, establishment_id)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    data: ClientUpdate,
    updater: ClientsUpdaterDep,
    actor: ActorDep,
) -> ClientRead:
    return await updater.update(client_id, data, actor, establishment_id)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    deleter: ClientsDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(client_id, actor, establishment_id)


@router.post("/{client_id}/activate", response_model=ClientRead)
async def activate_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    activator: ClientsActivatorDep,
    actor: ActorDep,
) -> ClientRead:
    return await activator.activate(client_id, actor, establishment_id)


@router.post("/{client_id}/deactivate", response_model=ClientRead)
async def deactivate_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    activator: ClientsActivatorDep,
    actor: ActorDep,
) -> ClientRead:
    return await activator.deactivate(client_id, actor, establishment_id)
