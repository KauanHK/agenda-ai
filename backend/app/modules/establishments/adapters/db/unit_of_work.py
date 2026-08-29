from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.establishments.adapters.db.repository import EstablishmentsRepository


class EstablishmentsUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """
        Inicializa a unidade de trabalho de estabelecimentos.

        Args:
            session_factory (Callable[[], AsyncSession]):
                Fábrica para criar sessões do banco de dados.
        """

        super().__init__(session_factory=session_factory)
        self._establishments: EstablishmentsRepository | None = None

    @property
    def establishments(self) -> EstablishmentsRepository:
        """Repositório de estabelecimentos."""
        if self._establishments is None:
            raise RuntimeError("Repositório de estabelecimentos não inicializado.")
        return self._establishments

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._establishments = EstablishmentsRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._establishments = None
