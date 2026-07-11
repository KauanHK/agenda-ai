from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.memberships.adapters.db.repository import MembershipsRepository
from app.modules.users.adapters.db.repository import UsersRepository


class MembershipsUnitOfWork(BaseUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:
        """
        Inicializa a unidade de trabalho de memberships.

        Args:
            session_factory (Callable[[], AsyncSession]):
                Fábrica para criar sessões do banco de dados.
        """

        super().__init__(session_factory=session_factory)
        self._memberships: MembershipsRepository | None = None
        self._users: UsersRepository | None = None

    @property
    def memberships(self) -> MembershipsRepository:
        """Repositório de memberships."""
        if self._memberships is None:
            raise RuntimeError("Repositório de memberships não inicializado.")
        return self._memberships

    @property
    def users(self) -> UsersRepository:
        """Repositório de usuários."""
        if self._users is None:
            raise RuntimeError("Repositório de usuários não inicializado.")
        return self._users

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._memberships = MembershipsRepository(self.session)
        self._users = UsersRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._memberships = None
        self._users = None
