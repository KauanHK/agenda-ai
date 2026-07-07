from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession


class RepositoryProtocol(Protocol):
    def __init__(self, session: AsyncSession) -> None: ...


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if exc_type is None:
            await self.commit()
            return
        await self.rollback()

    @property
    def session(self) -> AsyncSession:
        """Sessão atual do UnitOfWork."""
        return self._session

    async def commit(self) -> None:
        """Aplica o commit."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Aplica o rollback."""
        await self._session.rollback()

    def repository[T: RepositoryProtocol](self, repository_cls: type[T]) -> T:
        """
        Inicializa um repositório usando a sessão atual do UnitOfWork.

        Args:
            repository_cls (type[T]): A classe do repositório a ser inicializada.

        Returns:
            T: A instância do repositório inicializada com a sessão atual.
        """

        return repository_cls(self._session)
