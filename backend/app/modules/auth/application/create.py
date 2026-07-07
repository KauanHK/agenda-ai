from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security.passwords import hash_password
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.domain.model import Membership
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserCreate, UserRead
from app.modules.users.infra.repository import UsersRepository


class UsersCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(self, data: UserCreate, actor: UserActor) -> UserRead:
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
                data.establishment_id, [UserRole.ESTABLISHMENT_ADMIN]
            ):
                raise ForbiddenError(
                    "Usuário não pode criar usuários nesse estabelecimento"
                )
            if data.role != UserRole.MEMBER:
                raise ForbiddenError("establishment_admin só pode criar members")
            effective_establishment_id = data.establishment_id

        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = User(
                name=data.name,
                email=data.email,
                password_hash=hash_password(data.password),
            )

            try:
                created = await repo.create(user)
            except IntegrityError as e:
                raise ConflictError("E-mail já está em uso.") from e

            membership = Membership(
                user_id=created.id,
                establishment_id=effective_establishment_id,
                role=data.role,
            )
            membership_repo = self._uow.repository(MembershipRepository)
            await membership_repo.add(membership=membership)

            return UserRead.model_validate(created)
