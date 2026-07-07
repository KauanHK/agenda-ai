import uuid
from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.api.deps.auth import ActorDep, GlobalAdminActorDep
from app.modules.establishments.application.activate import EstablishmentsActivator
from app.modules.establishments.application.create import EstablishmentsCreator
from app.modules.establishments.application.delete import EstablishmentsDeleter
from app.modules.establishments.application.read import EstablishmentsReader
from app.modules.establishments.application.update import EstablishmentsUpdater
from app.modules.establishments.domain.model import Establishment
from app.modules.establishments.infra.repository import EstablishmentsRepository
from app.modules.memberships.api.deps import MembershipRepositoryDep


def get_establishments_repository(uow: UnitOfWorkDep) -> EstablishmentsRepository:
    return uow.repository(EstablishmentsRepository)


def get_establishments_activator(
    uow: UnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsActivator:
    return EstablishmentsActivator(uow=uow)


def get_establishments_creator(
    uow: UnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsCreator:
    return EstablishmentsCreator(uow=uow)


def get_establishments_deleter(
    uow: UnitOfWorkDep,
    _: GlobalAdminActorDep,
) -> EstablishmentsDeleter:
    return EstablishmentsDeleter(uow=uow)


def get_establishments_reader(uow: UnitOfWorkDep) -> EstablishmentsReader:
    return EstablishmentsReader(uow=uow)


def get_establishments_updater(uow: UnitOfWorkDep) -> EstablishmentsUpdater:
    return EstablishmentsUpdater(uow=uow)


async def get_establishment(
    establishment_id: uuid.UUID,
    actor: ActorDep,
    repository: Annotated[
        EstablishmentsRepository, Depends(get_establishments_repository)
    ],
    memberships_repository: MembershipRepositoryDep,
) -> Establishment:
    if not actor.is_member_of(establishment_id):
        await memberships_repository.get_by_user_and_establishment(
            user_id=actor.user_id,
            establishment_id=establishment_id,
        )

    return await repository.get_by_id(
        establishment_id=establishment_id,
    )


EstablishmentsActivatorDep = Annotated[
    EstablishmentsActivator, Depends(get_establishments_activator)
]

EstablishmentsCreatorDep = Annotated[
    EstablishmentsCreator, Depends(get_establishments_creator)
]

EstablishmentsDeleterDep = Annotated[
    EstablishmentsDeleter, Depends(get_establishments_deleter)
]

EstablishmentsReaderDep = Annotated[
    EstablishmentsReader, Depends(get_establishments_reader)
]

EstablishmentsUpdaterDep = Annotated[
    EstablishmentsUpdater, Depends(get_establishments_updater)
]

EstablishmentDep = Annotated[
    Establishment,
    Depends(get_establishment),
]
