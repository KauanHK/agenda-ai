from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.establishments.application.ports.repositories import (
    EstablishmentsRepositoryProtocol,
)


class EstablishmentsUnitOfWorkProtocol(Protocol):
    @property
    def establishments(self) -> EstablishmentsRepositoryProtocol: ...

    @property
    def session(self) -> AsyncSession: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
