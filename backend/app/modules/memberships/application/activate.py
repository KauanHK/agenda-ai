import uuid

from app.core.actors.user import UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.application._authz import assert_can_manage
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository


class MembershipActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> MembershipRead:
        return await self._set_active_status(
            user_id=user_id,
            establishment_id=establishment_id,
            is_active=True,
            actor=actor,
        )

    async def deactivate(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> MembershipRead:
        return await self._set_active_status(
            user_id=user_id,
            establishment_id=establishment_id,
            is_active=False,
            actor=actor,
        )

    async def _set_active_status(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
    ) -> MembershipRead:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            caller_membership = await repo.get_by_user_and_establishment_or_none(
                user_id=actor.user_id,
                establishment_id=establishment_id,
            )
            assert_can_manage(actor, caller_membership)

            membership = await repo.get_by_user_and_establishment(
                user_id=user_id,
                establishment_id=establishment_id,
            )
            membership.is_active = is_active
            await repo.update(membership)
            updated = await repo.get_by_user_and_establishment(
                user_id=user_id,
                establishment_id=establishment_id,
            )
            return MembershipRead.model_validate(updated)
