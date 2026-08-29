from types import TracebackType
from typing import Protocol, Self

from app.modules.unavailabilities.application.ports.repositories import (
    UnavailabilitiesRepositoryProtocol,
)


class UnavailabilitiesUnitOfWorkProtocol(Protocol):
    @property
    def unavailabilities(self) -> UnavailabilitiesRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
