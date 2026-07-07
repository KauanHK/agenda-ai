import enum
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from app.core.exceptions import UnauthorizedError
from app.core.security.jwt import create_token, decode_token
from app.core.settings import settings


class TokenType(enum.StrEnum):
    CLIENT = "client"


class SessionTokenPayload(TypedDict):
    type: TokenType
    client_id: uuid.UUID
    establishment_id: uuid.UUID
    phone: str
    iat: datetime
    exp: datetime


def create_client_mcp_session_token(
    client_id: uuid.UUID,
    establishment_id: uuid.UUID,
    phone: str,
) -> str:

    now = datetime.now(UTC)
    exp_minutes = timedelta(minutes=settings.MCP_SESSION_TOKEN_EXPIRES_MINUTES)

    payload = SessionTokenPayload(
        type=TokenType.CLIENT,
        client_id=str(client_id),
        establishment_id=str(establishment_id),
        phone=phone,
        iat=now,
        exp=now + exp_minutes,
    )

    return create_token(claims=payload)


def decode_client_mcp_session_token(
    token: str,
) -> SessionTokenPayload:
    """
    Decodifica um token de sessão do cliente MCP e retorna os dados contidos nele.
    Se o token for inválido ou expirado, uma exceção UnauthorizedError será levantada.
    """

    claims = decode_token(token=token)
    if claims.get("type") != TokenType.CLIENT:
        raise UnauthorizedError(f"Invalid token type {claims.get('type')}.")
    return SessionTokenPayload(**claims)
