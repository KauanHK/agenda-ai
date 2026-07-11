from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.roles import UserRole
from app.core.security.passwords import hash_password
from app.modules.auth.application.ports.unit_of_work import AuthUnitOfWorkProtocol
from app.modules.memberships.domain.entities import NewMembership
from app.modules.users.application.dtos.commands import CreateUserCommand
from app.modules.users.domain.entities import NewUser, User


class UsersCreator:
    def __init__(self, uow: AuthUnitOfWorkProtocol) -> None:
        """
        Inicializa um criador de usuários.

        Args:
            uow (AuthUnitOfWorkProtocol):
                Unit of work de autenticação.
        """

        self._uow = uow

    async def create(self, data: CreateUserCommand, actor: UserActor) -> User:
        """Cria um novo usuário e vincula-o a um estabelecimento."""

        if actor.is_global_admin:
            if (
                data.role == UserRole.ESTABLISHMENT_ADMIN
                and data.establishment_id is None
            ):
                raise ForbiddenError("establishment_id é obrigatório")
            effective_establishment_id = data.establishment_id
        else:
            if data.establishment_id is None:
                raise ForbiddenError("establishment_id é obrigatório")
            if not actor.has_role_in(
                data.establishment_id, {UserRole.ESTABLISHMENT_ADMIN}
            ):
                raise ForbiddenError(
                    "Usuário não pode criar usuários nesse estabelecimento"
                )
            if data.role != UserRole.MEMBER:
                raise ForbiddenError("establishment_admin só pode criar members")
            effective_establishment_id = data.establishment_id

        async with self._uow as uow:
            new_user = NewUser(
                name=data.name,
                email=data.email,
                password_hash=hash_password(data.password),
            )

            try:
                created = await uow.users.create(new_user)
            except IntegrityError as e:
                raise ConflictError("E-mail já está em uso.") from e

            await uow.memberships.create(
                NewMembership(
                    user_id=created.id,
                    establishment_id=effective_establishment_id,
                    role=data.role,
                )
            )

            return created
