"""Emissão da sessão do cliente no próprio processo, direto no banco."""

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.settings import settings
from app.modules.agent.domain.entities import BookingSession
from app.modules.agent.domain.exceptions import (
    BookingSessionError,
    ClientBlockedError,
    InvalidPhoneError,
)
from app.modules.booking.adapters.db.factories import make_unit_of_work
from app.modules.booking.application.ports.unit_of_work import BookingUnitOfWorkProtocol
from app.modules.booking.application.use_cases.sessions import CustomerSessionIssuer
from app.modules.booking.domain.entities import CustomerSession


class InProcessSessionIssuer:
    """Troca o telefone do cliente por uma sessão, chamando o caso de uso do booking.

    Implementa `BookingSessionIssuerProtocol`. Todo erro do backend é traduzido
    aqui num erro de domínio do agente: nenhuma exceção de banco sobe deste adapter.

    Um `ConflictError` significa que duas mensagens do mesmo cliente novo chegaram
    juntas e a outra criou o cadastro primeiro; uma nova tentativa (com um UoW novo)
    encontra o cliente e emite a sessão.
    """

    def __init__(
        self,
        *,
        establishment_id: uuid.UUID,
        clock: Callable[[], datetime],
        uow_factory: Callable[[], BookingUnitOfWorkProtocol] = make_unit_of_work,
    ) -> None:
        self._establishment_id = establishment_id
        self._clock = clock
        self._uow_factory = uow_factory

    async def issue(self, phone: str, name: str | None) -> BookingSession:
        """Emite a sessão do cliente a partir do telefone."""
        try:
            try:
                customer = await self._issue_once(phone, name)
            except ConflictError:
                customer = await self._issue_once(phone, name)
        except ForbiddenError as exc:
            raise ClientBlockedError("Cliente inativo no estabelecimento.") from exc
        except ValueError as exc:
            raise InvalidPhoneError("Telefone inválido para emitir a sessão.") from exc
        except (ConflictError, NotFoundError, SQLAlchemyError, OSError) as exc:
            raise BookingSessionError("Não foi possível emitir a sessão.") from exc

        return BookingSession(
            token=customer.token,
            phone=phone,
            client_id=customer.client_id,
            client_name=customer.client_name,
            expires_at=self._clock()
            + timedelta(minutes=settings.MCP_SESSION_TOKEN_EXPIRES_MINUTES),
            is_new_client=customer.is_new_client,
        )

    async def _issue_once(self, phone: str, name: str | None) -> CustomerSession:
        return await CustomerSessionIssuer(self._uow_factory()).issue(
            establishment_id=self._establishment_id,
            phone=phone,
            name=name,
        )
