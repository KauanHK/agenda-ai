"""
Token de sessão do cliente no servidor MCP.

Emitido pelo backend depois de identificar o cliente pelo telefone, e apresentado pelo
agente de IA como `Authorization: Bearer` a cada tool call. Carrega o contexto que o
LLM não pode escolher — `client_id`, `establishment_id` e telefone — de forma assinada.

Assinado com `AGENT_SESSION_SECRET`, separado do `JWT_SECRET` do painel: comprometer um
escopo não compromete o outro, e um access token do painel nunca é aceito aqui.
"""

import enum
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from app.core.exceptions import UnauthorizedError
from app.core.security.jwt import create_token, decode_token
from app.core.settings import settings


class TokenType(enum.StrEnum):
    CLIENT = "client"


class SessionTokenClaims(TypedDict):
    """Claims do token, como trafegam no JWT (ids serializados como string)."""

    type: str
    client_id: str
    establishment_id: str
    phone: str
    iat: datetime
    exp: datetime


class SessionTokenPayload(TypedDict):
    """Payload já convertido para os tipos do domínio."""

    type: str
    client_id: uuid.UUID
    establishment_id: uuid.UUID
    phone: str


def create_client_mcp_session_token(
    client_id: uuid.UUID,
    establishment_id: uuid.UUID,
    phone: str,
) -> str:
    """
    Cria o token de sessão de um cliente para o servidor MCP.

    Args:
        client_id (uuid.UUID): O cliente identificado pelo telefone.
        establishment_id (uuid.UUID): O estabelecimento da conversa.
        phone (str): O telefone do cliente, em formato canônico.

    Returns:
        str: O token de sessão assinado.
    """

    now = datetime.now(UTC)
    expires = timedelta(minutes=settings.MCP_SESSION_TOKEN_EXPIRES_MINUTES)

    claims = SessionTokenClaims(
        type=TokenType.CLIENT,
        client_id=str(client_id),
        establishment_id=str(establishment_id),
        phone=phone,
        iat=now,
        exp=now + expires,
    )

    return create_token(claims=claims, key=settings.AGENT_SESSION_SECRET)


def decode_client_mcp_session_token(token: str) -> SessionTokenPayload:
    """
    Decodifica um token de sessão do cliente e retorna o contexto contido nele.

    Args:
        token (str): O token de sessão, sem o prefixo `Bearer `.

    Returns:
        SessionTokenPayload: O contexto verificado da sessão.

    Raises:
        UnauthorizedError: Se o token for inválido, expirado ou de outro tipo.
    """

    claims = decode_token(token=token, key=settings.AGENT_SESSION_SECRET)

    if claims.get("type") != TokenType.CLIENT:
        raise UnauthorizedError(f"Invalid token type {claims.get('type')}.")

    try:
        return SessionTokenPayload(
            type=claims["type"],
            client_id=uuid.UUID(claims["client_id"]),
            establishment_id=uuid.UUID(claims["establishment_id"]),
            phone=claims["phone"],
        )
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed session token.") from exc
