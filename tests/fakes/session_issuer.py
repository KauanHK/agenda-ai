"""Fake de `BookingSessionIssuerProtocol` para os testes de aplicação."""

from src.domain.entities import BookingSession
from src.domain.exceptions import AgentError


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
        self.calls: list[tuple[str, str | None]] = []

    async def issue(self, phone: str, name: str | None) -> BookingSession:
        self.calls.append((phone, name))
        if self._error is not None:
            raise self._error
        assert self._session is not None, "FakeSessionIssuer sem sessão nem erro"
        return self._session
