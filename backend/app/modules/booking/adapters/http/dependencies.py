"""Dependências do endpoint de sessão do canal automático."""

import hmac
from typing import Annotated

from fastapi import Depends, Header

from app.core.exceptions import UnauthorizedError
from app.core.settings import settings
from app.modules.booking.adapters.db.factories import make_unit_of_work
from app.modules.booking.adapters.db.unit_of_work import BookingUnitOfWork

BookingUnitOfWorkDep = Annotated[BookingUnitOfWork, Depends(make_unit_of_work)]


def require_service_key(
    x_service_key: Annotated[str | None, Header(alias="X-Service-Key")] = None,
) -> None:
    """
    Exige a chave de serviço do canal automático.

    Emitir uma sessão significa assumir a identidade de um cliente a partir de um
    telefone, sem nenhuma prova de posse do número — quem faz essa prova é o WhatsApp,
    antes da mensagem chegar. Por isso o endpoint é máquina-a-máquina: só o
    orquestrador que recebe o webhook pode chamá-lo, e nunca deve ficar exposto
    publicamente.

    Args:
        x_service_key (str | None): A chave enviada no header `X-Service-Key`.

    Raises:
        UnauthorizedError: Se a chave estiver ausente ou não conferir.
    """

    if x_service_key is None or not hmac.compare_digest(
        x_service_key, settings.AGENT_SERVICE_KEY
    ):
        raise UnauthorizedError("Chave de serviço inválida.")


ServiceKeyDep = Depends(require_service_key)
