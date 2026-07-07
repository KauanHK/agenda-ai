import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.modules.users.domain.enums import UserRole


def assert_can_access(actor: UserActor, establishment_id: uuid.UUID) -> None:
    if actor.is_global_admin:
        raise ForbiddenError("global_admin não opera sobre agendamentos.")
    if not actor.is_member_of(establishment_id):
        raise ForbiddenError("Acesso negado a este estabelecimento.")


def assert_can_write(actor: UserActor, establishment_id: uuid.UUID) -> None:
    assert_can_access(actor, establishment_id)


def assert_can_admin(actor: UserActor, establishment_id: uuid.UUID) -> None:
    assert_can_access(actor, establishment_id)
    if not actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN}):
        raise ForbiddenError("Apenas establishment_admin pode realizar esta ação.")


def assert_can_manage(
    actor: UserActor,
    establishment_id: uuid.UUID,
    scheduling_user_id: uuid.UUID,
) -> None:
    """Permite admin ou o próprio profissional dono do agendamento."""
    assert_can_access(actor, establishment_id)
    is_admin = actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN})
    is_owner = actor.user_id == scheduling_user_id
    if not is_admin and not is_owner:
        raise ForbiddenError("Acesso negado a este agendamento.")
