import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security.access_tokens import decode_access_token


async def get_current_subject(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> uuid.UUID:
    """Decodifica o token de acesso e retorna o `sub` (id do usuário)."""

    claims = decode_access_token(authorization.credentials)
    return uuid.UUID(claims["sub"])


SubjectDep = Annotated[uuid.UUID, Depends(get_current_subject)]
