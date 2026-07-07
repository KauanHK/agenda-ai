from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.unavailabilities.application.create import UnavailabilitiesCreator
from app.modules.unavailabilities.application.delete import UnavailabilitiesDeleter
from app.modules.unavailabilities.application.read import UnavailabilitiesReader
from app.modules.unavailabilities.application.update import UnavailabilitiesUpdater


def get_unavailabilities_creator(uow: UnitOfWorkDep) -> UnavailabilitiesCreator:
    return UnavailabilitiesCreator(uow=uow)


def get_unavailabilities_reader(uow: UnitOfWorkDep) -> UnavailabilitiesReader:
    return UnavailabilitiesReader(uow=uow)


def get_unavailabilities_updater(uow: UnitOfWorkDep) -> UnavailabilitiesUpdater:
    return UnavailabilitiesUpdater(uow=uow)


def get_unavailabilities_deleter(uow: UnitOfWorkDep) -> UnavailabilitiesDeleter:
    return UnavailabilitiesDeleter(uow=uow)


UnavailabilitiesCreatorDep = Annotated[UnavailabilitiesCreator, Depends(get_unavailabilities_creator)]
UnavailabilitiesReaderDep = Annotated[UnavailabilitiesReader, Depends(get_unavailabilities_reader)]
UnavailabilitiesUpdaterDep = Annotated[UnavailabilitiesUpdater, Depends(get_unavailabilities_updater)]
UnavailabilitiesDeleterDep = Annotated[UnavailabilitiesDeleter, Depends(get_unavailabilities_deleter)]
