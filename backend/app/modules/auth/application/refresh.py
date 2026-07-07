import uuid

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.auth.domain.schemas import RefreshRequest, TokenResponse
from app.modules.users.infra.repository import UsersRepository


class AuthRefresh:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        claims = decode_refresh_token(data.refresh_token)

        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_id_or_none(uuid.UUID(claims["sub"]))

            if user is None or not user.is_active:
                raise UnauthorizedError("Usuário inativo ou não encontrado.")

            identity = TokenIdentity(subject=user.id)

            return TokenResponse(
                access_token=create_access_token(identity),
                refresh_token=create_refresh_token(identity),
            )
