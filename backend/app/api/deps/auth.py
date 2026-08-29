import uuid
from typing import Annotated

from fastapi import Depends

from app.core.actors.user import Membership, UserActor
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security.dependencies import SubjectDep
from app.modules.auth.adapters.http.dependencies import AuthUnitOfWorkDep


async def get_current_actor(
    user_id: SubjectDep,
    uow: AuthUnitOfWorkDep,
) -> UserActor:

    async with uow:
        user = await uow.users.get_by_id_or_none(user_id)

        if user is None or not user.is_active:
            raise UnauthorizedError("Usuário inativo ou não encontrado.")

        memberships = await uow.memberships.list_by_user(user.id)

    return UserActor(
        user_id=user.id,
        is_global_admin=user.is_global_admin,
        memberships=tuple(
            Membership(establishment_id=m.establishment_id, role=m.role)
            for m in memberships
        ),
    )


def get_current_global_admin_actor(
    actor: UserActor = Depends(get_current_actor),
) -> UserActor:
    if not actor.is_global_admin:
        raise ForbiddenError(
            "Acesso negado. Requer privilégios de administrador global."
        )
    return actor


async def get_current_establishment_actor(
    establishment_id: uuid.UUID,
    actor: Annotated[UserActor, Depends(get_current_actor)],
) -> UserActor:
    """
    Obtém o ator atual e garante que ele é membro do estabelecimento especificado.
    """

    if not actor.is_member_of(establishment_id):
        raise ForbiddenError("Acesso negado a este estabelecimento.")
    return actor


ActorDep = Annotated[UserActor, Depends(get_current_actor)]
GlobalAdminActorDep = Annotated[UserActor, Depends(get_current_global_admin_actor)]
EstablishmentActorDep = Annotated[UserActor, Depends(get_current_establishment_actor)]
