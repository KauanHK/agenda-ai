"""
Endpoint de sessão do canal automático.

Fica fora da árvore `/establishments/{id}` porque não é o painel quem chama: quem chama
é o orquestrador que recebe o webhook do WhatsApp, autenticado por chave de serviço em
vez de JWT de usuário.
"""

import uuid

from fastapi import APIRouter, status

from app.core.exceptions import ValidationAppError
from app.core.settings import settings
from app.modules.booking.adapters.http.dependencies import BookingUnitOfWorkDep
from app.modules.booking.adapters.http.schemas import (
    IssueSessionRequest,
    SessionClientRead,
    SessionRead,
)
from app.modules.booking.application.use_cases.sessions import CustomerSessionIssuer

router = APIRouter()


@router.post(
    "/{establishment_id}/sessions",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Emite o token de sessão de um cliente a partir do telefone",
)
async def issue_session(
    establishment_id: uuid.UUID,
    data: IssueSessionRequest,
    uow: BookingUnitOfWorkDep,
) -> SessionRead:
    """
    Identifica o cliente pelo telefone e devolve o token que o agente usará no MCP.

    O `establishment_id` vem da URL do webhook, nunca do conteúdo da mensagem. O
    cliente é criado se ainda não existir.
    """

    try:
        session = await CustomerSessionIssuer(uow).issue(
            establishment_id=establishment_id,
            phone=data.phone,
            name=data.name,
        )
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc

    return SessionRead(
        session_token=session.token,
        expires_in_minutes=settings.MCP_SESSION_TOKEN_EXPIRES_MINUTES,
        client=SessionClientRead(id=session.client_id, name=session.client_name),
        is_new_client=session.is_new_client,
    )
