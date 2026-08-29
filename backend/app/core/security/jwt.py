from collections.abc import Mapping
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.exceptions import UnauthorizedError
from app.core.settings import settings


def create_token(
    claims: Mapping[str, Any],
    key: str | None = None,
) -> str:
    """
    Cria um token JWT com os claims fornecidos.

    Args:
        claims (Mapping[str, Any]): Um dicionário contendo os claims a serem incluídos no token.
        key (str | None):
            Segredo de assinatura. Por padrão usa o `JWT_SECRET` do painel; tokens de
            outro escopo (ex.: sessão do cliente no MCP) passam o seu próprio.

    Returns:
        str: O token JWT gerado.
    """

    return jwt.encode(
        claims=dict(claims),
        key=key or settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(
    token: str,
    key: str | None = None,
) -> dict[str, Any]:
    """
    Decodifica um token JWT e retorna os claims contidos nele.
    Se o token for inválido ou expirado, uma exceção UnauthorizedError será levantada.

    Args:
        token (str): O token JWT a ser decodificado.
        key (str | None):
            Segredo de verificação. Deve ser o mesmo usado na assinatura.
    Returns:
        dict[str, Any]: Um dicionário contendo os claims decodificados do token.
    """

    try:
        return jwt.decode(
            token=token,
            key=key or settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise UnauthorizedError("Token expired.") from None
    except JWTError as exc:
        raise UnauthorizedError("Invalid token.") from exc
