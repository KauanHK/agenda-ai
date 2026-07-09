import logging
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseUnitOfWork:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """
        Inicializa a unidade de trabalho base.

        Args:
            session_factory (Callable[[], AsyncSession]):
                Fábrica para criar sessões do banco de dados.
        """

        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        """Sessão do banco de dados."""
        if self._session is None:
            raise RuntimeError("Sessão do banco de dados não inicializada.")
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self._handle_commit()
            else:
                await self._handle_rollback()
        finally:
            await self.session.close()

    async def _handle_rollback(self) -> None:
        """
        Tenta fazer rollback na sessão do banco de dados. Em caso de falha, loga o erro.
        """

        try:
            await self.session.rollback()
        except Exception:
            logger.error("Erro ao fazer rollback.", exc_info=True)

    async def _handle_commit(self) -> None:
        """
        Tenta fazer commit na sessão do banco de dados. Em caso de falha, loga o erro e
        faz rollback.
        """

        try:
            await self.session.commit()
        except Exception:
            logger.error("Erro ao fazer commit.", exc_info=True)
            await self._handle_rollback()
            raise
