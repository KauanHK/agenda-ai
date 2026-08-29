from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.messaging_templates.adapters.db.repository import (
    MessagingTemplatesRepository,
)
from app.modules.services.infra.repository import ServicesRepository


class MessagingTemplatesUnitOfWork(BaseUnitOfWork):
    """
    Unit of work de templates de mensagem. Expõe também o repositório de serviços
    (de outro módulo) para validar vínculos, na mesma sessão/transação.
    """

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """Inicializa a unidade de trabalho de templates de mensagem."""

        super().__init__(session_factory=session_factory)
        self._messaging_templates: MessagingTemplatesRepository | None = None
        self._services: ServicesRepository | None = None

    @property
    def messaging_templates(self) -> MessagingTemplatesRepository:
        """Repositório de templates de mensagem."""
        if self._messaging_templates is None:
            raise RuntimeError("Repositório de templates de mensagem não inicializado.")
        return self._messaging_templates

    @property
    def services(self) -> ServicesRepository:
        """Repositório de serviços (de outro módulo)."""
        if self._services is None:
            raise RuntimeError("Repositório de serviços não inicializado.")
        return self._services

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._messaging_templates = MessagingTemplatesRepository(self.session)
        self._services = ServicesRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._messaging_templates = None
        self._services = None
