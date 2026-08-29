from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.operating_hours.adapters.db.repository import (
    OperatingHoursRepository,
)


class OperatingHoursUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """
        Inicializa a unidade de trabalho de horários de funcionamento.

        Args:
            session_factory (Callable[[], AsyncSession]):
                Fábrica para criar sessões do banco de dados.
        """

        super().__init__(session_factory=session_factory)
        self._operating_hours: OperatingHoursRepository | None = None

    @property
    def operating_hours(self) -> OperatingHoursRepository:
        """Repositório de horários de funcionamento."""
        if self._operating_hours is None:
            raise RuntimeError("Repositório de horários de funcionamento não inicializado.")
        return self._operating_hours

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._operating_hours = OperatingHoursRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._operating_hours = None
