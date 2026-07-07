from typing import Annotated

from fastapi import Depends

from app.db.deps import get_unit_of_work
from app.db.unit_of_work import UnitOfWork

UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]
