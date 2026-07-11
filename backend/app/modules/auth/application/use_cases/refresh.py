import uuid

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.modules.auth.application.dtos.commands import RefreshCommand
from app.modules.auth.application.ports.unit_of_work import AuthUnitOfWorkProtocol
from app.modules.auth.domain.entities import TokenPair


class AuthRefresh:
    def __init__(self, uow: AuthUnitOfWorkProtocol) -> None:
        """
        Inicializa o serviço de atualização de tokens.

        Args:
            uow (AuthUnitOfWorkProtocol):
                Unit of work de autenticação.
        """

        self._uow = uow

    async def refresh(self, data: RefreshCommand) -> TokenPair:
        """Emite um novo par de tokens a partir de um refresh token válido."""

        claims = decode_refresh_token(data.refresh_token)

        async with self._uow as uow:
            user = await uow.users.get_by_id_or_none(uuid.UUID(claims["sub"]))

            if user is None or not user.is_active:
                raise UnauthorizedError("Usuário inativo ou não encontrado.")

            identity = TokenIdentity(subject=user.id)

            return TokenPair(
                access_token=create_access_token(identity),
                refresh_token=create_refresh_token(identity),
            )
