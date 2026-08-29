from typing import Annotated

from fastapi import Depends

from app.modules.unavailabilities.adapters.db.factories import make_unit_of_work
from app.modules.unavailabilities.adapters.db.unit_of_work import (
    UnavailabilitiesUnitOfWork,
)

UnavailabilitiesUnitOfWorkDep = Annotated[
    UnavailabilitiesUnitOfWork,
    Depends(make_unit_of_work),
]
