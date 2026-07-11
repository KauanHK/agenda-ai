import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.roles import UserRole
from app.modules.memberships.application.authz import (
    assert_can_manage,
    assert_not_last_admin,
)
from app.modules.memberships.application.ports.unit_of_work import (
    MembershipsUnitOfWorkProtocol,
)


class MembershipDeleter:
    def __init__(self, uow: MembershipsUnitOfWorkProtocol) -> None:
        """
        Inicializa um removedor de memberships.

        Args:
            uow (MembershipsUnitOfWorkProtocol):
                Unit of work de memberships.
        """

        self._uow = uow

    async def delete(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> None:
        """Remove o vínculo de um usuário com um estabelecimento."""

        async with self._uow as uow:
            caller_membership = (
                await uow.memberships.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
            )
            assert_can_manage(actor, caller_membership)

            membership = await uow.memberships.get_by_user_and_establishment_or_none(
                user_id, establishment_id
            )
            if membership is None:
                raise NotFoundError("Membership não encontrada.")

            if membership.role == UserRole.ESTABLISHMENT_ADMIN:
                admin_count = await uow.memberships.count_admins_in_establishment(
                    establishment_id
                )
                assert_not_last_admin(membership, admin_count)

            await uow.memberships.delete_by_user_and_establishment(
                user_id, establishment_id
            )
