from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.clients.adapters.db.repository import ClientsRepository


class ClientsUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """Inicializa a unidade de trabalho de clientes."""

        super().__init__(session_factory=session_factory)
        self._clients: ClientsRepository | None = None

    @property
    def clients(self) -> ClientsRepository:
        """Repositório de clientes."""
        if self._clients is None:
            raise RuntimeError("Repositório de clientes não inicializado.")
        return self._clients

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._clients = ClientsRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._clients = None
