import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.core.security.passwords import hash_password
from app.modules.memberships.application.authz import assert_can_manage
from app.modules.memberships.application.dtos.commands import (
    InviteExistingMemberCommand,
    InviteMemberCommand,
    InviteNewMemberCommand,
)
from app.modules.memberships.application.ports.unit_of_work import (
    MembershipsUnitOfWorkProtocol,
)
from app.modules.memberships.domain.entities import MembershipExpanded, NewMembership
from app.modules.users.domain.entities import NewUser


class MembershipCreator:
    def __init__(self, uow: MembershipsUnitOfWorkProtocol) -> None:
        """
        Inicializa um criador de memberships.

        Args:
            uow (MembershipsUnitOfWorkProtocol):
                Unit of work de memberships.
        """

        self._uow = uow

    async def create(
        self,
        establishment_id: uuid.UUID,
        data: InviteMemberCommand,
        actor: UserActor,
    ) -> MembershipExpanded:
        """Vincula um usuário (novo ou existente) a um estabelecimento."""

        async with self._uow as uow:
            caller_membership = (
                await uow.memberships.get_by_user_and_establishment_or_none(
                    user_id=actor.user_id,
                    establishment_id=establishment_id,
                )
            )
            assert_can_manage(actor, caller_membership)

            if isinstance(data, InviteExistingMemberCommand):
                user_id = data.user_id
            else:
                user_id = await self._create_user(uow, data)

            new_membership = NewMembership(
                user_id=user_id,
                establishment_id=establishment_id,
                role=data.role,
            )

            try:
                await uow.memberships.create(new_membership)
            except IntegrityError as e:
                raise ConflictError(
                    "Usuário já é membro deste estabelecimento."
                ) from e

            return await uow.memberships.get_by_user_and_establishment_expanded(
                user_id=user_id,
                establishment_id=establishment_id,
            )

    async def _create_user(
        self,
        uow: MembershipsUnitOfWorkProtocol,
        data: InviteNewMemberCommand,
    ) -> uuid.UUID:
        """Cria um novo usuário para o convite, quando não há usuário existente."""

        existing = await uow.users.get_by_email_or_none(data.email)
        if existing:
            raise ConflictError("Já existe um usuário com este e-mail.")

        new_user = NewUser(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
        )
        created = await uow.users.create(new_user)
        return created.id
