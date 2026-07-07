from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.operating_hours.application.read import OperatingHoursReader
from app.modules.operating_hours.application.update import OperatingHoursUpdater


def get_operating_hours_reader(uow: UnitOfWorkDep) -> OperatingHoursReader:
    return OperatingHoursReader(uow=uow)


def get_operating_hours_updater(uow: UnitOfWorkDep) -> OperatingHoursUpdater:
    return OperatingHoursUpdater(uow=uow)


OperatingHoursReaderDep = Annotated[OperatingHoursReader, Depends(get_operating_hours_reader)]
OperatingHoursUpdaterDep = Annotated[OperatingHoursUpdater, Depends(get_operating_hours_updater)]
