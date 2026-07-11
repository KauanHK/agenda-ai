from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
)
from app.core.security.passwords import verify_password
from app.modules.auth.application.dtos.commands import LoginCommand
from app.modules.auth.application.ports.unit_of_work import AuthUnitOfWorkProtocol
from app.modules.auth.domain.entities import TokenPair


class AuthLogin:
    def __init__(self, uow: AuthUnitOfWorkProtocol) -> None:
        """
        Inicializa o serviço de login.

        Args:
            uow (AuthUnitOfWorkProtocol):
                Unit of work de autenticação.
        """

        self._uow = uow

    async def login(self, data: LoginCommand) -> TokenPair:
        """
        Autentica um usuário e retorna os tokens de acesso e atualização.

        Args:
            data (LoginCommand): As credenciais do usuário.

        Returns:
            TokenPair: Os tokens de acesso e atualização.

        Raises:
            UnauthorizedError: Se as credenciais forem inválidas ou o usuário
                estiver inativo.
        """

        async with self._uow as uow:
            user = await uow.users.get_by_email_or_none(data.username)

            if user is None or not verify_password(data.password, user.password_hash):
                raise UnauthorizedError("Credenciais inválidas.")

            if not user.is_active:
                raise UnauthorizedError("Usuário inativo.")

            identity = TokenIdentity(subject=user.id)

            return TokenPair(
                access_token=create_access_token(identity),
                refresh_token=create_refresh_token(identity),
            )
