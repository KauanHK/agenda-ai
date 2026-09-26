"""Porta do diretório de canais: qual bot atende cada estabelecimento."""

import uuid
from typing import Protocol

from app.modules.agent.domain.entities import TelegramChannel


class TelegramChannelDirectoryProtocol(Protocol):
    """Descobre, pelo estabelecimento, o bot do Telegram que o atende."""

    async def get(self, establishment_id: uuid.UUID) -> TelegramChannel | None:
        """Devolve o canal do estabelecimento, ou `None` se ele não atende.

        Não atende quem não tem bot conectado, ou o estabelecimento inexistente,
        inativo ou excluído.

        Raises:
            ChannelLookupError: Se não foi possível consultar.
        """
        ...
