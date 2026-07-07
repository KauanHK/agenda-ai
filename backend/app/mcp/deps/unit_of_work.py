from fastmcp.dependencies import Depends

from app.api.deps.db import get_db_session


async def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[UnitOfWork]:
    """Dependência para obter uma instância de UnitOfWork."""

    async with UnitOfWork(session) as uow:
        yield uow


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]
