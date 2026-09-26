from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.channels.adapters.db.repository import TelegramBotsRepository
from app.modules.establishments.adapters.db.repository import EstablishmentsRepository


class ChannelsUnitOfWork(BaseUnitOfWork):
    """Unidade de trabalho dos canais de atendimento automático."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ) -> None:

        super().__init__(session_factory=session_factory)
        self._telegram_bots: TelegramBotsRepository | None = None
        self._establishments: EstablishmentsRepository | None = None

    @property
    def telegram_bots(self) -> TelegramBotsRepository:
        """Repositório de bots do Telegram."""
        return self._require(self._telegram_bots, "bots do Telegram")

    @property
    def establishments(self) -> EstablishmentsRepository:
        """Repositório de estabelecimentos."""
        return self._require(self._establishments, "estabelecimentos")

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        session = self.session
        self._telegram_bots = TelegramBotsRepository(session)
        self._establishments = EstablishmentsRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._telegram_bots = None
        self._establishments = None

    def _require[T](self, repository: T | None, name: str) -> T:
        if repository is None:
            raise RuntimeError(f"Repositório de {name} não inicializado.")
        return repository
