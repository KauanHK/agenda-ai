import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.establishments.api.deps import (
    EstablishmentsActivatorDep,
    EstablishmentsCreatorDep,
    EstablishmentsDeleterDep,
    EstablishmentsReaderDep,
    EstablishmentsUpdaterDep,
)
from app.modules.establishments.domain.schemas import (
    EstablishmentCreate,
    EstablishmentRead,
    EstablishmentUpdate,
)

router = APIRouter()


@router.post("", response_model=EstablishmentRead, status_code=201)
async def create_establishment(
    data: EstablishmentCreate,
    creator: EstablishmentsCreatorDep,
) -> EstablishmentRead:
    """Cria um novo estabelecimento."""

    return await creator.create(data)


@router.get("", response_model=PaginatedResponse[EstablishmentRead])
async def list_establishments(
    pagination: PaginationParamsDep,
    reader: EstablishmentsReaderDep,
    name: str | None = None,
    cnpj: str | None = None,
    timezone: str | None = None,
) -> PaginatedResponse[EstablishmentRead]:
    """Lista estabelecimentos com paginação e filtros opcionais."""

    return await reader.paginate(
        pagination=pagination,
        name=name,
        cnpj=cnpj,
        timezone=timezone,
    )


@router.get("/{establishment_id}", response_model=EstablishmentRead)
async def get_establishment(
    establishment_id: uuid.UUID,
    actor: ActorDep,
    reader: EstablishmentsReaderDep,
) -> EstablishmentRead:
    """Obtém um estabelecimento pelo ID."""

    return await reader.get_by_id(
        establishment_id=establishment_id,
        actor=actor,
    )


@router.patch("/{establishment_id}", response_model=EstablishmentRead)
async def update_establishment(
    establishment_id: uuid.UUID,
    data: EstablishmentUpdate,
    updater: EstablishmentsUpdaterDep,
) -> EstablishmentRead:
    """Atualiza parcialmente um estabelecimento existente."""

    return await updater.update(establishment_id, data)


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

    return await activator.activate(establishment_id)


@router.post("/{establishment_id}/deactivate", response_model=EstablishmentRead)
async def deactivate_establishment(
    establishment_id: uuid.UUID,
    activator: EstablishmentsActivatorDep,
) -> EstablishmentRead:
    """Desativa um estabelecimento existente."""

    return await activator.deactivate(establishment_id)
