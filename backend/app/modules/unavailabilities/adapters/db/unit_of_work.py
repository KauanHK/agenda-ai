from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.unavailabilities.adapters.db.repository import (
    UnavailabilitiesRepository,
)


class UnavailabilitiesUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """Inicializa a unidade de trabalho de unavailabilities."""

        super().__init__(session_factory=session_factory)
        self._unavailabilities: UnavailabilitiesRepository | None = None

    @property
    def unavailabilities(self) -> UnavailabilitiesRepository:
        """Repositório de unavailabilities."""
        if self._unavailabilities is None:
            raise RuntimeError("Repositório de unavailabilities não inicializado.")
        return self._unavailabilities

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._unavailabilities = UnavailabilitiesRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._unavailabilities = None
