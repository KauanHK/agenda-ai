from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.memberships.domain.model import Membership
from app.modules.users.domain.enums import UserRole


def assert_can_manage(
    actor: UserActor,
    caller_membership: Membership | None,
) -> None:
    """Verifica se o ator pode gerenciar memberships no estabelecimento."""
    if actor.is_global_admin:
        return
    if (
        caller_membership is None
        or caller_membership.role != UserRole.ESTABLISHMENT_ADMIN
    ):
        raise ForbiddenError(
            "Apenas administradores do estabelecimento podem gerenciar memberships."
        )


def assert_not_last_admin(membership: Membership, admin_count: int) -> None:
    """Garante que a operação não removerá o último administrador do estabelecimento."""
    if membership.role == UserRole.ESTABLISHMENT_ADMIN and admin_count <= 1:
        raise ConflictError(
            "Não é possível rebaixar ou remover o último administrador do estabelecimento."
        )
