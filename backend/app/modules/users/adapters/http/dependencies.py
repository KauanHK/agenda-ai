from typing import Annotated

from fastapi import Depends

from app.modules.users.adapters.db.factories import make_unit_of_work
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork
from app.modules.users.application.use_cases.activate import UsersActivator
from app.modules.users.application.use_cases.delete import UsersDeleter
from app.modules.users.application.use_cases.read import UsersReader
from app.modules.users.application.use_cases.update import UsersUpdater

UsersUnitOfWorkDep = Annotated[UsersUnitOfWork, Depends(make_unit_of_work)]


def get_users_reader(uow: UsersUnitOfWorkDep) -> UsersReader:
    return UsersReader(uow=uow)


def get_users_updater(uow: UsersUnitOfWorkDep) -> UsersUpdater:
    return UsersUpdater(uow=uow)


def get_users_activator(uow: UsersUnitOfWorkDep) -> UsersActivator:
    return UsersActivator(uow=uow)


def get_users_deleter(uow: UsersUnitOfWorkDep) -> UsersDeleter:
    return UsersDeleter(uow=uow)


UsersReaderDep = Annotated[UsersReader, Depends(get_users_reader)]
UsersUpdaterDep = Annotated[UsersUpdater, Depends(get_users_updater)]
UsersActivatorDep = Annotated[UsersActivator, Depends(get_users_activator)]
UsersDeleterDep = Annotated[UsersDeleter, Depends(get_users_deleter)]
