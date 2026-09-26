"""Fake de `BookingSessionIssuerProtocol` para os testes de aplicação."""

import uuid

from app.modules.agent.domain.entities import BookingSession
from app.modules.agent.domain.exceptions import AgentError


class FakeSessionIssuer:
    """Devolve uma sessão roteirizada (ou levanta) e conta as emissões."""

    def __init__(
        self,
        session: BookingSession | None = None,
        *,
        error: AgentError | None = None,
    ) -> None:
        self._session = session
        self._error = error
        self.calls: list[tuple[uuid.UUID, str, str | None]] = []

    async def issue(
        self, establishment_id: uuid.UUID, phone: str, name: str | None
    ) -> BookingSession:
        self.calls.append((establishment_id, phone, name))
        if self._error is not None:
            raise self._error
        assert self._session is not None, "FakeSessionIssuer sem sessão nem erro"
        return self._session
