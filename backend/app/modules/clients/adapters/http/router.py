import uuid

from fastapi import APIRouter, Response

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.params import Page
from app.core.pagination.schemas import (
    PaginatedResponse,
    build_paginated_response_from_page,
)
from app.modules.clients.adapters.http.dependencies import ClientsUnitOfWorkDep
from app.modules.clients.adapters.http.schemas import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
)
from app.modules.clients.application.dtos.commands import (
    CreateClientCommand,
    UpdateClientCommand,
)
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.application.use_cases.activate import ClientsActivator
from app.modules.clients.application.use_cases.create import ClientsCreator
from app.modules.clients.application.use_cases.delete import ClientsDeleter
from app.modules.clients.application.use_cases.paginator import ClientsPaginator
from app.modules.clients.application.use_cases.read import ClientsReader
from app.modules.clients.application.use_cases.update import ClientsUpdater

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ClientRead])
async def list_clients(
    establishment_id: uuid.UUID,
    page_params: PageParamsDep,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
    q: str | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse[ClientRead]:
    page = await ClientsPaginator(uow=uow).paginate(
        page_params=page_params,
        actor=actor,
        establishment_id=establishment_id,
        filters=ClientFilters(q=q, is_active=is_active),
    )
    return build_paginated_response_from_page(
        Page(
            items=[ClientRead.model_validate(c.to_dict()) for c in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
    )


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> ClientRead:
    client = await ClientsReader(uow=uow).get_by_id(
        client_id, actor, establishment_id
    )
    return ClientRead.model_validate(client.to_dict())


@router.post("", response_model=ClientRead, status_code=201)
async def create_client(
    establishment_id: uuid.UUID,
    data: ClientCreate,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> ClientRead:
    client = await ClientsCreator(uow=uow).create(
        CreateClientCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return ClientRead.model_validate(client.to_dict())


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    data: ClientUpdate,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> ClientRead:
    client = await ClientsUpdater(uow=uow).update(
        client_id,
        UpdateClientCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return ClientRead.model_validate(client.to_dict())


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> Response:
    await ClientsDeleter(uow=uow).delete(client_id, actor, establishment_id)
    return Response(status_code=204)


@router.post("/{client_id}/activate", response_model=ClientRead)
async def activate_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> ClientRead:
    client = await ClientsActivator(uow=uow).activate(
        client_id, actor, establishment_id
    )
    return ClientRead.model_validate(client.to_dict())


@router.post("/{client_id}/deactivate", response_model=ClientRead)
async def deactivate_client(
    establishment_id: uuid.UUID,
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
    actor: ActorDep,
) -> ClientRead:
    client = await ClientsActivator(uow=uow).deactivate(
        client_id, actor, establishment_id
    )
    return ClientRead.model_validate(client.to_dict())
