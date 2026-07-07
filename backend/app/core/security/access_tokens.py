import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from app.core.exceptions import UnauthorizedError
from app.core.security.jwt import create_token, decode_token
from app.core.settings import settings


@dataclass(frozen=True, slots=True)
class TokenIdentity:
    subject: uuid.UUID


class Claims(TypedDict):
    sub: str
    type: str
    iat: datetime
    exp: datetime


def create_access_token(
    identity: TokenIdentity,
) -> str:
    """
    Cria um token de acesso JWT para o usuário especificado.

    Args:
        identity (TokenIdentity): O identificador do usuário (sub).
    Returns:
        str: O token de acesso JWT gerado.
    """

    now = datetime.now(tz=UTC)
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)
    return create_token(
        claims=Claims(
            sub=str(identity.subject),
            type="access",
            iat=now,
            exp=now + expires,
        )
    )


def create_refresh_token(
    identity: TokenIdentity,
) -> str:
    """
    Cria um token de atualização JWT para o usuário especificado.

    Args:
        identity (TokenIdentity): O identificador do usuário (sub).
    Returns:
        str: O token de atualização JWT gerado.
    """

    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    now = datetime.now(tz=UTC)
    return create_token(
        claims=Claims(
            sub=str(identity.subject),
            type="refresh",
            iat=now,
            exp=now + expires,
        )
    )


def decode_access_token(token: str) -> Claims:
    """
    Decodifica um token de acesso JWT e retorna os claims contidos nele.
    Se o token for inválido ou expirado, uma exceção UnauthorizedError será levantada.

    Args:
        token (str): O token de acesso JWT a ser decodificado.
    Returns:
        Claims: Um dicionário contendo os claims decodificados do token.
    """

    claims = decode_token(token=token)
    if claims.get("type") != "access":
        raise UnauthorizedError(f"Invalid token type {claims.get('type')}.")
    return Claims(**claims)


def decode_refresh_token(token: str) -> Claims:
    """
    Decodifica um token de atualização JWT e retorna os claims contidos nele.
    Se o token for inválido ou expirado, uma exceção UnauthorizedError será levantada.

    Args:
        token (str): O token de atualização JWT a ser decodificado.
    Returns:
        Claims: Um dicionário contendo os claims decodificados do token.
    """

    claims = decode_token(token=token)
    if claims.get("type") != "refresh":
        raise UnauthorizedError(f"Invalid token type {claims.get('type')}.")
    return Claims(**claims)
