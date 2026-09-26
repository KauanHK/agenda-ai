import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.modules.users.domain.enums import UserRole

# Diferente de `operating_hours`, o `global_admin` pode conectar e desconectar de
# propósito: é ele quem faz o onboarding do estabelecimento.


def assert_can_read(actor: UserActor, establishment_id: uuid.UUID) -> None:
    if not actor.is_member_of(establishment_id):
        raise ForbiddenError("Acesso negado a este estabelecimento.")


def assert_can_manage(actor: UserActor, establishment_id: uuid.UUID) -> None:
    if actor.is_global_admin:
        return
    if not actor.has_role_in(establishment_id, {UserRole.ESTABLISHMENT_ADMIN}):
        raise ForbiddenError(
            "Apenas establishment_admin pode conectar ou desconectar o bot."
        )
