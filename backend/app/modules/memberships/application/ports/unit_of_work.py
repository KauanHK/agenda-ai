from types import TracebackType
from typing import Protocol, Self

from app.modules.memberships.application.ports.repositories import (
    MembershipsRepositoryProtocol,
)
from app.modules.users.application.ports.repositories import UsersRepositoryProtocol


class MembershipsUnitOfWorkProtocol(Protocol):
    @property
    def memberships(self) -> MembershipsRepositoryProtocol: ...

    @property
    def users(self) -> UsersRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
