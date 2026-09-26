from types import TracebackType
from typing import Protocol, Self

from app.modules.channels.application.ports.repositories import (
    TelegramBotsRepositoryProtocol,
)
from app.modules.establishments.application.ports.repositories import (
    EstablishmentsRepositoryProtocol,
)


class ChannelsUnitOfWorkProtocol(Protocol):
    """
    Contrato da unidade de trabalho dos canais.

    Traz os estabelecimentos junto porque conectar um bot e rotear uma mensagem
    precisam saber se o estabelecimento existe, se está ativo e qual é o fuso.
    """

    @property
    def telegram_bots(self) -> TelegramBotsRepositoryProtocol: ...

    @property
    def establishments(self) -> EstablishmentsRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
