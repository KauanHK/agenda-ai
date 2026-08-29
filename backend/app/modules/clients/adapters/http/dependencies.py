from typing import Annotated

from fastapi import Depends

from app.modules.clients.adapters.db.factories import make_unit_of_work
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork

ClientsUnitOfWorkDep = Annotated[ClientsUnitOfWork, Depends(make_unit_of_work)]
