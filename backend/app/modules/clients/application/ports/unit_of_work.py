from types import TracebackType
from typing import Protocol, Self

from app.modules.clients.application.ports.repositories import (
    ClientsRepositoryProtocol,
)


class ClientsUnitOfWorkProtocol(Protocol):
    @property
    def clients(self) -> ClientsRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
