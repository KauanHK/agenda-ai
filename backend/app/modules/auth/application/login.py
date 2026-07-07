from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
)
from app.core.security.passwords import verify_password
from app.db.unit_of_work import UnitOfWork
from app.modules.auth.domain.schemas import LoginRequest, TokenResponse
from app.modules.users.infra.repository import UsersRepository


class AuthLogin:
    def __init__(self, uow: UnitOfWork) -> None:
        """
        Inicializa o serviço de login.

        Args:
            uow (UnitOfWork):
                A unidade de trabalho para acessar os repositórios.
        """

        self._uow = uow

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Autentica um usuário e retorna os tokens de acesso e atualização.

        Args:
            data (LoginRequest): As credenciais do usuário.

        Returns:
            TokenResponse: Os tokens de acesso e atualização.

        Raises:
            UnauthorizedError: Se as credenciais forem inválidas ou o usuário estiver inativo.
        """

        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_email_or_none(data.username)

            if user is None or not verify_password(data.password, user.password_hash):
                raise UnauthorizedError("Credenciais inválidas.")

            if not user.is_active:
                raise UnauthorizedError("Usuário inativo.")

            identity = TokenIdentity(
                subject=user.id,
            )

            return TokenResponse(
                access_token=create_access_token(identity),
                refresh_token=create_refresh_token(identity),
            )
