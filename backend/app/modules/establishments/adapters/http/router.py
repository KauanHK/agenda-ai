import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse
from app.modules.establishments.adapters.http.dependencies import (
    EstablishmentsActivatorDep,
    EstablishmentsCreatorDep,
    EstablishmentsDeleterDep,
    EstablishmentsPaginatorDep,
    EstablishmentsReaderDep,
    EstablishmentsUpdaterDep,
)
from app.modules.establishments.adapters.http.schemas import (
    EstablishmentCreate,
    EstablishmentRead,
    EstablishmentUpdate,
)
from app.modules.establishments.application.dtos.commands import (
    CreateEstablishmentCommand,
    UpdateEstablishmentCommand,
)
from app.modules.establishments.application.dtos.filters import EstablishmentFilters

router = APIRouter()


@router.post("", response_model=EstablishmentRead, status_code=201)
async def create_establishment(
    data: EstablishmentCreate,
    creator: EstablishmentsCreatorDep,
) -> EstablishmentRead:
    """Cria um novo estabelecimento."""

    establishment = await creator.create(
        data=CreateEstablishmentCommand(**data.model_dump(exclude_unset=True))
    )
    return EstablishmentRead.model_validate(establishment.to_dict())


@router.get("", response_model=PaginatedResponse[EstablishmentRead])
async def list_establishments(
    page_params: PageParamsDep,
    paginator: EstablishmentsPaginatorDep,
    name: str | None = None,
    cnpj: str | None = None,
    timezone: str | None = None,
) -> PaginatedResponse[EstablishmentRead]:
    """Lista estabelecimentos com paginação e filtros opcionais."""

    page = await paginator.paginate(
        page_params=page_params,
        filters=EstablishmentFilters(name=name, document=cnpj, timezone=timezone),
    )
    return PaginatedResponse[EstablishmentRead](
        data=[EstablishmentRead.model_validate(e.to_dict()) for e in page.items],
        total=page.total,
        page=page.page,
        size=page.page_size,
    )


@router.get("/{establishment_id}", response_model=EstablishmentRead)
async def get_establishment(
    establishment_id: uuid.UUID,
    actor: ActorDep,
    reader: EstablishmentsReaderDep,
) -> EstablishmentRead:
    """Obtém um estabelecimento pelo ID."""

    establishment = await reader.get_by_id(
        establishment_id=establishment_id,
        actor=actor,
    )
    return EstablishmentRead.model_validate(establishment.to_dict())


@router.patch("/{establishment_id}", response_model=EstablishmentRead)
async def update_establishment(
    establishment_id: uuid.UUID,
    data: EstablishmentUpdate,
    updater: EstablishmentsUpdaterDep,
) -> EstablishmentRead:
    """Atualiza parcialmente um estabelecimento existente."""

    establishment = await updater.update(
        establishment_id,
        UpdateEstablishmentCommand(**data.model_dump(exclude_unset=True)),
    )
    return EstablishmentRead.model_validate(establishment.to_dict())


@router.delete("/{establishment_id}", status_code=204)
async def delete_establishment(
    establishment_id: uuid.UUID,
    deleter: EstablishmentsDeleterDep,
) -> None:
    """Exclui um estabelecimento existente."""

    await deleter.delete(establishment_id)


@router.post("/{establishment_id}/activate", response_model=EstablishmentRead)
async def activate_establishment(
    establishment_id: uuid.UUID,
    activator: EstablishmentsActivatorDep,
) -> EstablishmentRead:
    """Ativa um estabelecimento existente."""

    establishment = await activator.activate(establishment_id)
    return EstablishmentRead.model_validate(establishment.to_dict())


@router.post("/{establishment_id}/deactivate", response_model=EstablishmentRead)
async def deactivate_establishment(
    establishment_id: uuid.UUID,
    activator: EstablishmentsActivatorDep,
) -> EstablishmentRead:
    """Desativa um estabelecimento existente."""

    establishment = await activator.deactivate(establishment_id)
    return EstablishmentRead.model_validate(establishment.to_dict())
