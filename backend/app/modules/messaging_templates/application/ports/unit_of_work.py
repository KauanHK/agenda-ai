from types import TracebackType
from typing import Protocol, Self

from app.modules.messaging_templates.application.ports.repositories import (
    MessagingTemplatesRepositoryProtocol,
    ServicesQueryProtocol,
)


class MessagingTemplatesUnitOfWorkProtocol(Protocol):
    @property
    def messaging_templates(self) -> MessagingTemplatesRepositoryProtocol: ...

    @property
    def services(self) -> ServicesQueryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
