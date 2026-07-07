import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps.db import UnitOfWorkDep
from app.core.actors.user import Membership, UserActor
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security.access_tokens import decode_access_token
from app.modules.memberships.infra.repository import MembershipRepository
from app.modules.users.infra.repository import UsersRepository


async def get_current_actor(
    uow: UnitOfWorkDep,
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> UserActor:

    claims = decode_access_token(authorization.credentials)
    user_id = uuid.UUID(claims["sub"])

    async with uow:
        users_repo = uow.repository(UsersRepository)
        user = await users_repo.get_by_id_or_none(user_id)

        if user is None or not user.is_active:
            raise UnauthorizedError("Usuário inativo ou não encontrado.")

        memberships_repo = uow.repository(MembershipRepository)
        memberships = await memberships_repo.list_by_user(user_id)

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
