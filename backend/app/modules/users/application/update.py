import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security.passwords import hash_password
from app.db.unit_of_work import UnitOfWork
from app.modules.users.domain.schemas import UserRead, UserUpdate
from app.modules.users.infra.repository import UsersRepository


class UsersUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        id: uuid.UUID,
        data: UserUpdate,
        actor: UserActor,
    ) -> UserRead:
        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_id(id)

            if not actor.is_global_admin:
                raise ForbiddenError("Acesso negado.")

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(user, field, value)

            try:
                updated = await repo.update(user)
            except IntegrityError as e:
                raise ConflictError("E-mail já está em uso.") from e

            return UserRead.model_validate(updated)

    async def update_me(
        self,
        data: UserUpdate,
        actor: UserActor,
    ) -> UserRead:
        try:
            async with self._uow:
                repo = self._uow.repository(UsersRepository)
                user = await repo.get_by_id(actor.user_id)

                for field, value in data.model_dump(exclude_unset=True).items():
                    if field == "password":
                        user.password_hash = hash_password(value)
                    else:
                        setattr(user, field, value)

                updated = await repo.update(user)
                return UserRead.model_validate(updated)
        except IntegrityError as e:
            raise ConflictError("E-mail já está em uso.") from e
