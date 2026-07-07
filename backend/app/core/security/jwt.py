from collections.abc import Mapping
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.exceptions import UnauthorizedError
from app.core.settings import settings


def create_token(
    claims: Mapping[str, Any],
) -> str:
    """
    Cria um token JWT com os claims fornecidos.

    Args:
        claims (Mapping[str, Any]): Um dicionário contendo os claims a serem incluídos no token.

    Returns:
        str: O token JWT gerado.
    """

    return jwt.encode(
        claims=dict(claims),
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decodifica um token JWT e retorna os claims contidos nele.
    Se o token for inválido ou expirado, uma exceção UnauthorizedError será levantada.

    Args:
        token (str): O token JWT a ser decodificado.
    Returns:
        dict[str, Any]: Um dicionário contendo os claims decodificados do token.
    """

    try:
        return jwt.decode(
            token=token,
            key=settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise UnauthorizedError("Token expired.") from None
    except JWTError as exc:
        raise UnauthorizedError("Invalid token.") from exc
