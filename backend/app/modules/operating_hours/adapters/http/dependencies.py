from typing import Annotated

from fastapi import Depends

from app.modules.operating_hours.adapters.db.factories import make_unit_of_work
from app.modules.operating_hours.adapters.db.unit_of_work import (
    OperatingHoursUnitOfWork,
)
from app.modules.operating_hours.application.use_cases.read import (
    OperatingHoursReader,
)
from app.modules.operating_hours.application.use_cases.update import (
    OperatingHoursUpdater,
)

OperatingHoursUnitOfWorkDep = Annotated[
    OperatingHoursUnitOfWork, Depends(make_unit_of_work)
]


def get_operating_hours_reader(
    uow: OperatingHoursUnitOfWorkDep,
) -> OperatingHoursReader:
    return OperatingHoursReader(uow=uow)


def get_operating_hours_updater(
    uow: OperatingHoursUnitOfWorkDep,
) -> OperatingHoursUpdater:
    return OperatingHoursUpdater(uow=uow)


OperatingHoursReaderDep = Annotated[
    OperatingHoursReader, Depends(get_operating_hours_reader)
]
OperatingHoursUpdaterDep = Annotated[
    OperatingHoursUpdater, Depends(get_operating_hours_updater)
]
