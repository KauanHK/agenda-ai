from typing import Annotated

from fastapi import Depends

from app.core.db.session import db
from app.modules.memberships.adapters.db.factories import make_unit_of_work
from app.modules.memberships.adapters.db.repository import MembershipsRepository
from app.modules.memberships.adapters.db.unit_of_work import MembershipsUnitOfWork
from app.modules.memberships.application.use_cases.activate import (
    MembershipActivator,
)
from app.modules.memberships.application.use_cases.create import MembershipCreator
from app.modules.memberships.application.use_cases.delete import MembershipDeleter
from app.modules.memberships.application.use_cases.read import MembershipsReader
from app.modules.memberships.application.use_cases.update import MembershipUpdater

MembershipsUnitOfWorkDep = Annotated[
    MembershipsUnitOfWork, Depends(make_unit_of_work)
]


def get_membership_creator(uow: MembershipsUnitOfWorkDep) -> MembershipCreator:
    return MembershipCreator(uow=uow)


def get_membership_reader(uow: MembershipsUnitOfWorkDep) -> MembershipsReader:
    return MembershipsReader(uow=uow)


def get_membership_deleter(uow: MembershipsUnitOfWorkDep) -> MembershipDeleter:
    return MembershipDeleter(uow=uow)


def get_membership_updater(uow: MembershipsUnitOfWorkDep) -> MembershipUpdater:
    return MembershipUpdater(uow=uow)


def get_membership_activator(uow: MembershipsUnitOfWorkDep) -> MembershipActivator:
    return MembershipActivator(uow=uow)


def get_memberships_repository() -> MembershipsRepository:
    """
    Compat: fornece o repositório de memberships fora de uma unit of work, para
    consumidores que ainda dependem de acesso direto ao repositório.
    """

    return MembershipsRepository(db.create_session())


MembershipCreatorDep = Annotated[MembershipCreator, Depends(get_membership_creator)]
MembershipReaderDep = Annotated[MembershipsReader, Depends(get_membership_reader)]
MembershipDeleterDep = Annotated[MembershipDeleter, Depends(get_membership_deleter)]
MembershipUpdaterDep = Annotated[MembershipUpdater, Depends(get_membership_updater)]
MembershipActivatorDep = Annotated[
    MembershipActivator, Depends(get_membership_activator)
]
MembershipRepositoryDep = Annotated[
    MembershipsRepository, Depends(get_memberships_repository)
]
