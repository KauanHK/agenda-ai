"""
Dependências de identidade das tools.

O ator vem sempre do token verificado — nunca de um argumento da tool. É o que impede
que uma injeção de prompt convença o LLM a agendar em nome de outro cliente: mesmo que
ele tentasse, não existe parâmetro para isso.
"""

import uuid

from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from app.core.actors.customer import CustomerActor


async def get_customer_actor(
    token: AccessToken = CurrentAccessToken(),
) -> CustomerActor:
    """
    Monta o ator do cliente a partir dos claims do token de sessão.

    Args:
        token (AccessToken): O token já verificado por `SessionTokenVerifier`.

    Returns:
        CustomerActor: O cliente autenticado e o estabelecimento da conversa.
    """

    claims = token.claims or {}
    return CustomerActor(
        establishment_id=uuid.UUID(claims["establishment_id"]),
        client_id=uuid.UUID(claims["client_id"]),
        phone=claims["phone"],
    )
