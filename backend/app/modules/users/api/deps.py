from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.users.application.activate import UsersActivator
from app.modules.users.application.delete import UsersDeleter
from app.modules.users.application.read import UsersReader
from app.modules.users.application.update import UsersUpdater
from app.modules.users.domain.schemas import UsersFilters


def get_users_reader(uow: UnitOfWorkDep) -> UsersReader:
    return UsersReader(uow=uow)


def get_users_updater(uow: UnitOfWorkDep) -> UsersUpdater:
    return UsersUpdater(uow=uow)


def get_users_activator(uow: UnitOfWorkDep) -> UsersActivator:
    return UsersActivator(uow=uow)


def get_users_deleter(uow: UnitOfWorkDep) -> UsersDeleter:
    return UsersDeleter(uow=uow)


def get_user_filters(
    user_filters: Annotated[UsersFilters, Depends()],
) -> UsersFilters:
    return user_filters


UsersReaderDep = Annotated[UsersReader, Depends(get_users_reader)]
UsersUpdaterDep = Annotated[UsersUpdater, Depends(get_users_updater)]
UsersActivatorDep = Annotated[UsersActivator, Depends(get_users_activator)]
UsersDeleterDep = Annotated[UsersDeleter, Depends(get_users_deleter)]
UsersFiltersDep = Annotated[UsersFilters, Depends(get_user_filters)]
