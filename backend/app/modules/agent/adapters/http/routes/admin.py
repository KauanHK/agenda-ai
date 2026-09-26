"""Rotas administrativas do webhook do Telegram.

`POST /admin/telegram/webhook` registra o webhook na Bot API apontando para a
base pública informada; `GET /admin/telegram/webhook` consulta o que está
registrado, direto do Telegram. Nada é persistido aqui — quem guarda a URL é o
Telegram. É um passo de *bootstrap*, feito uma vez por ambiente depois do
primeiro deploy (ver `docs/09`).

As duas exigem `Authorization: Bearer <AGENT_TELEGRAM__ADMIN_TOKEN>`; sem ele, `401`.
"""

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.agent.adapters.http.dependencies import ContainerDep
from app.modules.agent.domain.exceptions import WebhookRegistrationError

router = APIRouter(prefix="/admin/telegram")

# `auto_error=False` para responder `401` (e não o `403` padrão) quando o header falta.
_bearer = HTTPBearer(auto_error=False)


def _require_admin(
    container: ContainerDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """Compara o Bearer com o token configurado em tempo constante."""
    supplied = credentials.credentials if credentials is not None else ""
    if not hmac.compare_digest(supplied, container.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token administrativo inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/webhook", dependencies=[Depends(_require_admin)])
async def register_webhook(
    container: ContainerDep,
    base_url: Annotated[str, Body(embed=True)],
    drop_pending_updates: Annotated[bool, Body(embed=True)] = False,
) -> dict[str, Any]:
    """Registra o webhook na base pública HTTPS dada e devolve o `getWebhookInfo`.

    Corpo: `{"base_url": "https://agente.exemplo", "drop_pending_updates": false}`.
    O Telegram só aceita HTTPS, então a checagem é feita aqui (`422`) antes de
    bater na Bot API.
    """
    if not base_url.startswith("https://"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="base_url precisa começar com https://",
        )
    try:
        return await container.register_webhook(base_url, drop_pending_updates)
    except WebhookRegistrationError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from None


@router.get("/webhook", dependencies=[Depends(_require_admin)])
async def get_webhook(container: ContainerDep) -> dict[str, Any]:
    """Devolve o `getWebhookInfo` atual (segredo mascarado na `url`)."""
    try:
        return await container.get_webhook_info()
    except WebhookRegistrationError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from None
