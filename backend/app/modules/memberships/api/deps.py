from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.memberships.application.activate import MembershipActivator
from app.modules.memberships.application.create import MembershipCreator
from app.modules.memberships.application.delete import MembershipDeleter
from app.modules.memberships.application.read import MembershipsReader
from app.modules.memberships.application.update import MembershipUpdater
from app.modules.memberships.infra.repository import MembershipRepository


def get_memberships_repository(uow: UnitOfWorkDep) -> MembershipRepository:
    return uow.repository(MembershipRepository)


def get_membership_creator(uow: UnitOfWorkDep) -> MembershipCreator:
    return MembershipCreator(uow=uow)


def get_membership_reader(uow: UnitOfWorkDep) -> MembershipsReader:
    return MembershipsReader(uow=uow)


def get_membership_deleter(uow: UnitOfWorkDep) -> MembershipDeleter:
    return MembershipDeleter(uow=uow)


def get_membership_updater(uow: UnitOfWorkDep) -> MembershipUpdater:
    return MembershipUpdater(uow=uow)


def get_membership_activator(uow: UnitOfWorkDep) -> MembershipActivator:
    return MembershipActivator(uow=uow)


MembershipRepositoryDep = Annotated[
    MembershipRepository, Depends(get_memberships_repository)
]
MembershipCreatorDep = Annotated[MembershipCreator, Depends(get_membership_creator)]
MembershipReaderDep = Annotated[MembershipsReader, Depends(get_membership_reader)]
MembershipDeleterDep = Annotated[MembershipDeleter, Depends(get_membership_deleter)]
MembershipUpdaterDep = Annotated[MembershipUpdater, Depends(get_membership_updater)]
MembershipActivatorDep = Annotated[MembershipActivator, Depends(get_membership_activator)]
