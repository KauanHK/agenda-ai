import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application._authz import assert_can_manage
from app.modules.memberships.domain.expanded import MembershipReadExpanded
from app.modules.memberships.domain.model import Membership
from app.modules.memberships.domain.schemas import (
    MembershipInviteExisting,
    MembershipInviteNew,
    MembershipInvitePayload,
)
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.model import User
from app.modules.users.infra.repository import UsersRepository


class MembershipCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        establishment_id: uuid.UUID,
        data: MembershipInvitePayload,
        actor: UserActor,
    ) -> MembershipReadExpanded:

        async with self._uow:
            membership_repo = self._uow.repository(MembershipRepository)

            caller_membership = (
                await membership_repo.get_by_user_and_establishment_or_none(
                    establishment_id=establishment_id,
                    user_id=actor.user_id,
                )
            )
            assert_can_manage(actor, caller_membership)

            if isinstance(data, MembershipInviteExisting):
                user_id = data.user_id
            else:
                user_id = await self._create_user(data)

            membership = Membership(
                user_id=user_id,
                establishment_id=establishment_id,
                role=data.role,
            )

            try:
                membership = await membership_repo.add(membership)
            except IntegrityError as e:
                raise ConflictError("Usuário já é membro deste estabelecimento.") from e

            return MembershipReadExpanded.model_validate(membership)

    async def _create_user(self, data: MembershipInviteNew) -> uuid.UUID:
        user_repo = self._uow.repository(UsersRepository)

        existing = await user_repo.get_by_email_or_none(data.email)
        if existing:
            raise ConflictError("Já existe um usuário com este e-mail.")

        user = User(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password=data.password,
        )

        user = await user_repo.create(user)

        return user.id
