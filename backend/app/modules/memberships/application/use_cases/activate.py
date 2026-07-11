import uuid

from app.core.actors.user import UserActor
from app.modules.memberships.application.authz import assert_can_manage
from app.modules.memberships.application.ports.unit_of_work import (
    MembershipsUnitOfWorkProtocol,
)
from app.modules.memberships.domain.entities import MembershipWithUser, UpdateMembership


class MembershipActivator:
    def __init__(self, uow: MembershipsUnitOfWorkProtocol) -> None:
        """
        Inicializa um ativador de memberships.

        Args:
            uow (MembershipsUnitOfWorkProtocol):
                Unit of work de memberships.
        """

        self._uow = uow

    async def activate(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> MembershipWithUser:
        """Ativa uma membership."""

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
    ) -> MembershipWithUser:
        """Inativa uma membership."""

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
    ) -> MembershipWithUser:
        async with self._uow as uow:
            caller_membership = (
                await uow.memberships.get_by_user_and_establishment_or_none(
                    user_id=actor.user_id,
                    establishment_id=establishment_id,
                )
            )
            assert_can_manage(actor, caller_membership)

            return await uow.memberships.update_by_user_and_establishment(
                user_id,
                establishment_id,
                UpdateMembership(is_active=is_active),
            )
