import uuid
from typing import Annotated

from fastapi import Depends

from app.api.deps.auth import ActorDep, GlobalAdminActorDep
from app.modules.establishments.adapters.db.factories import make_unit_of_work
from app.modules.establishments.adapters.db.unit_of_work import (
    EstablishmentsUnitOfWork,
)
from app.modules.establishments.application.use_cases.activate import (
    EstablishmentsActivator,
)
from app.modules.establishments.application.use_cases.create import (
    EstablishmentsCreator,
)
from app.modules.establishments.application.use_cases.delete import (
    EstablishmentsDeleter,
)
from app.modules.establishments.application.use_cases.paginator import (
    EstablishmentsPaginator,
)
from app.modules.establishments.application.use_cases.read import EstablishmentsReader
from app.modules.establishments.application.use_cases.update import (
    EstablishmentsUpdater,
)
from app.modules.establishments.domain.entities import Establishment
from app.modules.memberships.api.deps import MembershipRepositoryDep

EstablishmentsUnitOfWorkDep = Annotated[
    EstablishmentsUnitOfWork, Depends(make_unit_of_work)
]


def get_establishments_creator(
    uow: EstablishmentsUnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsCreator:
    return EstablishmentsCreator(uow=uow)


def get_establishments_reader(uow: EstablishmentsUnitOfWorkDep) -> EstablishmentsReader:
    return EstablishmentsReader(uow=uow)


def get_establishments_paginator(
    uow: EstablishmentsUnitOfWorkDep,
) -> EstablishmentsPaginator:
    return EstablishmentsPaginator(uow=uow)


def get_establishments_updater(
    uow: EstablishmentsUnitOfWorkDep,
) -> EstablishmentsUpdater:
    return EstablishmentsUpdater(uow=uow)


def get_establishments_deleter(
    uow: EstablishmentsUnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsDeleter:
    return EstablishmentsDeleter(uow=uow)


def get_establishments_activator(
    uow: EstablishmentsUnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsActivator:
    return EstablishmentsActivator(uow=uow)


async def get_establishment(
    establishment_id: uuid.UUID,
    actor: ActorDep,
    uow: EstablishmentsUnitOfWorkDep,
    memberships_repository: MembershipRepositoryDep,
) -> Establishment:
    if not actor.is_member_of(establishment_id):
        await memberships_repository.get_by_user_and_establishment(
            user_id=actor.user_id,
            establishment_id=establishment_id,
        )

    async with uow:
        return await uow.establishments.get_by_id(establishment_id)


EstablishmentsCreatorDep = Annotated[
    EstablishmentsCreator, Depends(get_establishments_creator)
]

EstablishmentsReaderDep = Annotated[
    EstablishmentsReader, Depends(get_establishments_reader)
]

EstablishmentsPaginatorDep = Annotated[
    EstablishmentsPaginator, Depends(get_establishments_paginator)
]

EstablishmentsUpdaterDep = Annotated[
    EstablishmentsUpdater, Depends(get_establishments_updater)
]

EstablishmentsDeleterDep = Annotated[
    EstablishmentsDeleter, Depends(get_establishments_deleter)
]

EstablishmentsActivatorDep = Annotated[
    EstablishmentsActivator, Depends(get_establishments_activator)
]

EstablishmentDep = Annotated[
    Establishment,
    Depends(get_establishment),
]

__all__ = [
    "EstablishmentDep",
    "EstablishmentsActivatorDep",
    "EstablishmentsCreatorDep",
    "EstablishmentsDeleterDep",
    "EstablishmentsPaginatorDep",
    "EstablishmentsReaderDep",
    "EstablishmentsUnitOfWorkDep",
    "EstablishmentsUpdaterDep",
]
