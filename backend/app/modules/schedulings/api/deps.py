from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.schedulings.application.create import SchedulingsCreator
from app.modules.schedulings.application.read import SchedulingsReader
from app.modules.schedulings.application.update import SchedulingsUpdater


def get_schedulings_creator(uow: UnitOfWorkDep) -> SchedulingsCreator:
    return SchedulingsCreator(uow=uow)


def get_schedulings_reader(uow: UnitOfWorkDep) -> SchedulingsReader:
    return SchedulingsReader(uow=uow)


def get_schedulings_updater(uow: UnitOfWorkDep) -> SchedulingsUpdater:
    return SchedulingsUpdater(uow=uow)


SchedulingsCreatorDep = Annotated[SchedulingsCreator, Depends(get_schedulings_creator)]
SchedulingsReaderDep = Annotated[SchedulingsReader, Depends(get_schedulings_reader)]
SchedulingsUpdaterDep = Annotated[SchedulingsUpdater, Depends(get_schedulings_updater)]
