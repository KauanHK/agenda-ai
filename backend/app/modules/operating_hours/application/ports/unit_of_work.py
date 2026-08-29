from types import TracebackType
from typing import Protocol, Self

from app.modules.operating_hours.application.ports.repositories import (
    OperatingHoursRepositoryProtocol,
)


class OperatingHoursUnitOfWorkProtocol(Protocol):
    @property
    def operating_hours(self) -> OperatingHoursRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
