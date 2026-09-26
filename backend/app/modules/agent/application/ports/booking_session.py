"""Porta de emissão da sessão autenticada do cliente no AgendaBot."""

import uuid
from typing import Protocol

from app.modules.agent.domain.entities import BookingSession


class BookingSessionIssuerProtocol(Protocol):
    """Troca um telefone por uma sessão autenticada no AgendaBot."""

    async def issue(
        self, establishment_id: uuid.UUID, phone: str, name: str | None
    ) -> BookingSession:
        """Emite a sessão do cliente no estabelecimento a partir do telefone.

        Raises:
            ClientBlockedError: Se o cliente está inativo no estabelecimento.
            BookingSessionError: Em qualquer outra falha de emissão.
        """
        ...
