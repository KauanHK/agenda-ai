import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application._authz import (
    assert_can_manage,
    assert_not_last_admin,
)
from app.modules.memberships.domain.schemas import MembershipRead, MembershipUpdate
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.domain.enums import UserRole


class MembershipUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        data: MembershipUpdate,
        actor: UserActor,
    ) -> MembershipRead:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            caller_membership = await repo.get_by_user_and_establishment_or_none(
                actor.user_id, establishment_id
            )
            assert_can_manage(actor, caller_membership)

            membership = await repo.get_by_user_and_establishment_or_none(
                user_id, establishment_id
            )
            if membership is None:
                raise NotFoundError("Membership não encontrada.")

            if (
                membership.role == UserRole.ESTABLISHMENT_ADMIN
                and data.role != UserRole.ESTABLISHMENT_ADMIN
            ):
                admin_count = await repo.count_admins_in_establishment(establishment_id)
                assert_not_last_admin(membership, admin_count)

            membership.role = data.role
            updated = await repo.update(membership)
            return MembershipRead.model_validate(updated)
